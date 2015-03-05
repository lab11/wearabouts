FROM	ubuntu:14.04

RUN apt-get update

# Install tiller
RUN apt-get -y install ruby
RUN gem install tiller

# Install python packages
RUN apt-get install -y python-pip
RUN pip install pyserial socketIO-client pika

# Copy my app source code
ADD	bleScanner	/

RUN mkdir /logs

CMD	["/usr/local/bin/tiller", "-b", "/tiller"]
