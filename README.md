# framer
Extract values from binary StorX raw data files.

Required is Python 3.7.3+

The frame definitions are JSON files described in the documentation
and sample templates in the examples directory.

In typical Unix process style, there are multiple programs which can be
piped together to handle the processing.
   A full stream is ilke this:

	framer.py package.file data.file |
	fitter.py package.file |
	validator.py package.file |
	reduce-selection.py package.file |
	averager.py |
	viewer.py > results.tsv

Without any processing (or at any step thereafter) stats on the data can be
obtained:

	framer.py package.file data.file |
	data-ranges.py

	framer.py package.file data.file |
	reduce-selection.py package.file |
	data-stats.py
