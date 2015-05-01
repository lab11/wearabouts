
all: apartment.dat analyze.gnuplot twodays.gnuplot
	gnuplot analyze.gnuplot
	epstopdf analyze.eps
	gnuplot twodays.gnuplot
	epstopdf twodays.eps
	evince twodays.pdf


clean:
	rm analyze.eps
	rm analyze.pdf

