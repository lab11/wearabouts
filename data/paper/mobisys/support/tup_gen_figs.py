#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import os
import re
import string
import sys


# Pattern for parsing variables in filenames
STR_SPLIT_PERIOD = re.compile(r'''((?:[^."']|"[^"]*"|'[^']*')+)''')
STR_SPLIT_COMMA  = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')

# Static lists for gnuplot parsing
GPI_OUTPUT_STR = ["o", "ou", "out", "outp", "outpu", "output"]
GPI_PLOT_STR   = ["p", "pl", "plo", "plot"]

rel_dir = sys.argv[1]

# Substitute variables in [possible] filename strings
def substitute (var_dict, s):
	parts = STR_SPLIT_PERIOD.split(s)[1::2]
	result = ""

	for p in parts:
		if p[0] == '"' or p[0] == "'":
			result += p.strip("\"'")
		else:
			try:
				result += var_dict[p]
			except KeyError:
				return ""

	return result

# Parse gnuplot files for input and ouput files and print Tup rules
def gnuplot_rules (fnames):
	plt_num = 0
	for fname in fnames:
		f = open(fname)

		output_files = []
		input_files = []
		variables = {}

		while True:
			l = f.readline()
			if len(l) == 0:
				# EOF
				break

			l = l.strip()
			if len(l) == 0:
				# Blank line
				continue

			if l[0] == "#":
				# Skip any commented lines
				continue

			cmd = l.split()

			if len(cmd) > 1 and cmd[0] == "set" and cmd[1] in GPI_OUTPUT_STR:
				# This line contains an output filename
				# Need to save it to the output list
				outp = l.split()
				filename = substitute(variables, outp[2])
				if filename not in output_files:
					output_files.append(filename)
				continue

			if len(cmd) > 0 and cmd[0] in GPI_PLOT_STR:

				# Remove the "plot" keyword
				try:
					pline = l.split(None, 1)[1]
				except IndexError:
					# This was a blank plot command so we should just skip it
					continue

				# Concantenate all of the lines of the plot command
				pline_full = ""
				while True:
					pline = pline.strip(" \n")
					if len(pline) == 0:
						break
					elif pline[-1] == "\\":
						pline_full += pline[0:-1]
						pline = f.readline()
					else:
						pline_full += pline
						break

				# Separate all of the possible plot commands by commas
				plots = STR_SPLIT_COMMA.split(pline_full)[1::2]

				# Iterate over all of the lines in the plot
				for p in plots:
					# Get all the arguments to this particular line
					pargs = p.split()

					if len(pargs) == 0:
						# Empty line in the plot command. Skip
						continue

					# Take the first one (which is the filename), substitute any
					# variables, and then append it to our list of input files
					filename = substitute(variables, pargs[0])
					# Make sure the filename is actually a filename
					# Could be trying to plot a function.
					# Use the following heuristic:
					#   - all filenames have at least one .
					#   - all filenames have a letter following the last .
					if '.' in filename:
						chunks = filename.split('.')
						if chunks[-1][0].lower() in string.ascii_lowercase:
							# Make sure we haven't already added it
							if filename not in input_files:
								input_files.append(filename)

				continue

			# Check for a variable declaration
			# This line isn't completely correct, as an '=' inside a string
			# will trigger this, but (I think) leaving it this way for now won't
			# cause any problems.
			if "=" in l:
				var = l.split("=")
				variables[var[0].strip()] = var[1].strip("\" \n")
				continue

		inputs = " ".join(input_files)
		outputs = " ".join(output_files)

		print(": foreach {fname} | {inputs} |> gnuplot %f |> {outputs} {rel_dir}/<figspsgroup> {{epss{plt_num}}}".format(fname=fname,
		                                                                                                                 inputs=inputs,
		                                                                                                                 outputs=outputs,
		                                                                                                                 plt_num=plt_num,
		                                                                                                                 rel_dir=rel_dir))
		print(": foreach {{epss{plt_num}}} |> ^ CAPCONVERT %f ^ a2ping $(A2PING_OPTS) %f -o %o |> %B.pdf {rel_dir}/<figsgroup>".format(plt_num=plt_num,
		                                                                                                                               rel_dir=rel_dir))

		plt_num += 1



# Get all gnuplot files
gpi = glob.glob("*.plt") + glob.glob("*.gpi") + glob.glob("*.gnuplot")
gnuplot_rules(gpi)

# Could add other figure generators here...



