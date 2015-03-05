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


var rmq = amqp.createConnection(config.rabbitmq);

console.log('start')

rmq.on('ready', function () {
	console.log('connected to rabbitmq server');

	// xch = rmq.exchange(config.rabbitmq.exchange);
	rmq.exchange('wearabouts', {'durable': true, 'autoDelete': false}, function (xch) {
		console.log('Connected to exchange');

		getmac.getMac(function (err, mac_address) {
			if (err) {
				console.log('Could not get MAC address.');
				console.log(err);
			} else {
				console.log(mac_address);

				noble.on('stateChange', function (state) {
					console.log(state);
					if (state === 'poweredOn') {
						noble.startScanning([], true);
					}
				});

				noble.on('discover', function (peripheral) {
					manufac_data = '';

					console.log('peripheral discovered (' + peripheral.uuid.match(/../g).join(':') + '):');
					console.log('\thello my local name is:');
					console.log('\t\t' + peripheral.advertisement.localName);
					console.log('\tcan I interest you in any of the following advertised services:');
					console.log('\t\t' + JSON.stringify(peripheral.advertisement.serviceUuids));
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

					xch.publish('scanner.bleScanner.'+mac_address.toUpperCase(), blob);
				});
			}

		});

	});


});

rmq.on('error', function (e) {
	console.log('RabbitMQ Error: ' + e);
});
