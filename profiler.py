import inspect
from time import perf_counter
from collections import defaultdict
import re
import numpy as np

# TODO: make this work with functions called over multiple lines
#  (and the indentation issues this can cause - eg a 2 line if statement with indent on the second line)

# TODO: make work with args (for now only works with kwargs as these can be added to scope

def _indent(line):
	return (len(line) - len(line.lstrip('\t')))

def _match_indent(line1, line2):
	"""Modify line2 to match line1's indent"""
	ntabs = _indent(line1)
	return '\t' * ntabs + line2

def skip_line(line:str):
	if line.lstrip().startswith(('for ', 'while ', 'if ', 'else:', 'elif ')):
		return True
	if line.strip() == '':
		return True
	return False

def write_html(lines, values):
	html = '<body>'
	vmin, vmax = min(values), max(values)
	for l, v in zip(lines, values):
		rval = 255 * (v - vmin) / (vmax - vmin)
		rvalhex = hex(int(255 - rval))[-2:].replace('x', '0')

		textcol = 'white' if rval > 150 else 'black'

		l = l.replace('\t', '&emsp;')
		line = f"<font color={textcol} style='BACKGROUND-COLOR:#{rvalhex}{rvalhex}{rvalhex}; display:block;'>{l}<br></font>"
		html += '\n'+line
	html += '\n</body>'

	with open('out.html', 'w') as outfile:
		outfile.write(html)

def profile_func(func):
	def wrapper(*args, **kwargs):
		read_func = inspect.getsource(func)
		lines = read_func.split('\n')

		def_line = lines[1]
		mod_def_line = def_line.replace(f'def {func.__name__}', 'def profiled_func')
		base_indent = _indent(def_line)
		out_lines = [mod_def_line.lstrip('\t')]

		__profile_line_log = defaultdict(list)

		out_lines.append(_match_indent(lines[2][base_indent:], '___t=perf_counter()'))
		for n, line in enumerate(lines[2:-2]):
			line = line[base_indent:]
			out_lines.append(line)
			if not skip_line(line):
				out_lines.append(_match_indent(line, f'__profile_line_log[{n+2}].append(perf_counter() - ___t)'))
				out_lines.append(_match_indent(line, '___t=perf_counter()'))

		scope = {'perf_counter': perf_counter, '__profile_line_log': __profile_line_log, **globals(), **locals()}
		# print('\n'.join(out_lines))
		exec('\n'.join(out_lines), scope)
		res = scope['profiled_func'](*args, **kwargs)

		# print("Line    |  Tot Elapsed (us)  | Mean  Elapsed (us)")
		# for k, v in __profile_line_log.items():
		# 	print(f'{k}     | {sum(v)*1e6:.1f} | {np.mean(v)*1e6:.1f}')

		times = [sum(__profile_line_log.get(i, [0])) for i in range(len(lines))]
		write_html(lines, times)

		return res

	return wrapper