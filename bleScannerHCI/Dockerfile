FROM	ubuntu:14.04

RUN apt-get update

# Install curl (apparently we're in the minimalist view of the world w/ ubuntu)
RUN	apt-get install -y --force-yes -q curl

# Install bluetooth tools
RUN apt-get install -y --force-yes -q bluetooth bluez-utils libbluetooth-dev

# Install node
RUN	curl -sL https://deb.nodesource.com/setup | sudo bash -
RUN	sudo apt-get install -y nodejs

# Install tiller
RUN apt-get -y install ruby
RUN gem install tiller

# Copy my app source code
ADD	bleScannerHCI	/

# Install node requirements
RUN	npm install

ENV NOBLE_HCI_DEVICE_ID 1

CMD	["/usr/local/bin/tiller", "-b", "/tiller"]
