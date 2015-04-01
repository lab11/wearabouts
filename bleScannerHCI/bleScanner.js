#!/usr/bin/env node

/*
 * This scanner uses a typical BLE dongle to scan for advertisement packets.
 */

try {
    var config = require('/etc/wearabouts/bleScanner/config');
} catch (e) {
    var config = require('./config');
}

var amqp = require('amqp');
var getmac = require('getmac');
var noble = require('noble');

var devices = {}
var last_clean = Date.now()/1000

function clean_devices() {
    // just delete all of the devices for now. It will mean sending a couple of
    //  duplicate packets here and there, but is overall easier
    devices = {}
}

// Connect to the RabbitMQ instance that will be receiving all of our
// found packets.
var rmq = amqp.createConnection(config.rabbitmq);
rmq.on('ready', function () {

    // Need to connect to the correct exchange in order to publish packets
    rmq.exchange(config.rabbitmq.exchange, {'durable': true, 'autoDelete': false}, function (xch) {

        // Use our MAC address as a source identifier for this scanner
        getmac.getMac(function (err, mac_address) {
            if (err) {
                console.log('Could not get MAC address.');
                console.log(err);
            } else {
                console.log('Found mac address: ' + mac_address);

                noble.on('discover', function (peripheral) {
                    manufac_data = '';

                    //console.log('peripheral discovered (' + peripheral.uuid.match(/../g).join(':') + '):');
                    //console.log('\thello my local name is: ' + peripheral.advertisement.localName);
                    //console.log('\t\t' + peripheral.rssi);

                    if (peripheral.advertisement.manufacturerData) {
                        manufac_data = peripheral.advertisement.manufacturerData.toString('hex');
                    }

                    current_time = Date.now()/1000;
                    blob = {
                        location_str: 'unknown',
                        ble_addr: peripheral.uuid.match(/../g).join(':'),
                        name: peripheral.advertisement.localName,
                        scanner_macAddr: mac_address.toUpperCase(),
                        service_uuids: peripheral.advertisement.serviceUuids,
                        manufacturer_data: manufac_data,
                        rssi: peripheral.rssi,
                        time: current_time,
                    }

                    // create device if not existing
                    if (!(blob['ble_addr'] in devices)) {
                        devices[blob['ble_addr']] = {};
                        devices[blob['ble_addr']]['timestamp'] = 0;
                    }

                    // check if this packet should actually be transmitted. Rate limit to one per second
                    if (devices[blob['ble_addr']]['timestamp'] < current_time) {

                        // publish advertisement to RabbitMQ
                        console.log(blob['ble_addr'] + '  ' + peripheral.rssi);
                        xch.publish('experimental.scanner.bleScanner.'+mac_address.toUpperCase(), blob);
                    }

                    // update timestamp
                    devices[blob['ble_addr']]['timestamp'] = current_time;

                    // remove devices that haven't been seen in a while
                    if ((current_time - last_clean) > 12*60*60) {
                        last_clean = current_time;
                        clean_devices();
                    }
                });
            }

        });

    });
});

// Actually start receiving BLE advertisements
noble.on('stateChange', function (state) {
    console.log("Starting scan...");
    if (state === 'poweredOn') {
        noble.startScanning([], true);
    }
});

rmq.on('error', function (e) {
    console.log('RabbitMQ Error: ' + e);
});
