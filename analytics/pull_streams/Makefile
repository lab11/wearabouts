
all: data_rssi.dat analyze.gnuplot
	gnuplot analyze.gnuplot
	epstopdf analyze.eps
	evince analyze.pdf

clean:
	rm analyze.eps
	rm analyze.pdf

