#!/usr/bin/env node

/*
 * This scanner uses a typical BLE dongle to scan for advertisement packets.
 */

var getmac = require('getmac');
var noble = require('noble');
var fs = require('fs');

// look for a target device
//var target_ble_addr = 'f9:97:1e:8b:e7:27'; // brghena fitbit
//var target_ble_addr = 'e8:2c:76:b7:f7:8f'; // nordic beacon
var target_ble_addr = 'ed:95:16:b8:52:01'; // squall!
if (process.argv.length == 3) {
    target_ble_addr = process.argv[2];
}

// statistics
var start_time = Date.now()/1000;
var packet_count = 0;

// make a file to write to
var file = fs.createWriteStream("rssi.dat");

// start process once file is writeable
file.once('open', function(fd) {
        // file header
        file.write('# time\t\trssi\n');

		// Use our MAC address as a source identifier for this scanner
		getmac.getMac(function (err, mac_address) {
			if (err) {
				console.log('Could not get MAC address.');
				console.log(err);
			} else {
				//console.log('Found mac address: ' + mac_address);

				noble.on('discover', function (peripheral) {
					manufac_data = '';

                    var ble_addr = peripheral.uuid.match(/../g).join(':');
                    //console.log(ble_addr + ' ?= ' + target_ble_addr);
                    if (ble_addr != target_ble_addr) {
                        return;
                    }
                    var curr_time = Date.now()/1000

					//console.log('peripheral discovered (' + ble_addr + '):');
					//console.log('\tlocal name: ' + peripheral.advertisement.localName);
					//console.log('\t\t' + peripheral.rssi);
                    packet_count += 1;
                    console.log((curr_time - start_time) + ' -- ' + packet_count);

					if (peripheral.advertisement.manufacturerData) {
						manufac_data = peripheral.advertisement.manufacturerData.toString('hex');
					}

					blob = {
						location_str: 'unknown',
						ble_addr: ble_addr,
						name: peripheral.advertisement.localName,
						scanner_macAddr: mac_address.toUpperCase(),
						service_uuids: peripheral.advertisement.serviceUuids,
						manufacturer_data: manufac_data,
						rssi: peripheral.rssi,
						time: curr_time,
					}

                    // actually write to the file
                    file.write(blob.time + '\t\t' + blob.rssi + '\n');
				});
			}

		});
});


// Actually start receiving BLE advertisements
noble.on('stateChange', function (state) {
    console.log("Starting scan...");
    if (state === 'poweredOn') {
        noble.startScanning([], true);
    }
});

