#!/usr/bin/env node

/*
 * This scanner uses a typical BLE dongle to scan for advertisement packets.
 */

try {
	var config = require('/etc/wearabouts/bleScanner/config');
} catch (e) {
	var config = require('config')
}

var amqp = require('amqp');
var getmac = require('getmac');
var noble = require('noble');


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

				// Actually start receiving BLE advertisements
				noble.on('stateChange', function (state) {
					console.log(state);
					if (state === 'poweredOn') {
						noble.startScanning([], true);
					}
				});

				noble.on('discover', function (peripheral) {
					manufac_data = '';

					console.log('peripheral discovered (' + peripheral.uuid.match(/../g).join(':') + '):');
					console.log('\thello my local name is: ' + peripheral.advertisement.localName);
					console.log('\t\t' + peripheral.rssi);

					if (peripheral.advertisement.manufacturerData) {
						manufac_data = peripheral.advertisement.manufacturerData.toString('hex');
					}

					blob = {
						ble_addr: peripheral.uuid.match(/../g).join(':'),
						name: peripheral.advertisement.localName,
						scanner_macAddr: mac_address.toUpperCase(),
						service_uuids: peripheral.advertisement.serviceUuids,
						manufacturer_data: manufac_data,
						rssi: peripheral.rssi,
						time: Date.now()/1000,
					}

					// Publish advertisement to RabbitMQ
					xch.publish('scanner.bleScanner.'+mac_address.toUpperCase(), blob);
				});
			}

		});

	});


});

rmq.on('error', function (e) {
	console.log('RabbitMQ Error: ' + e);
});
