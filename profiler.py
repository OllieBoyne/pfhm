import inspect
from time import perf_counter
from collections import defaultdict, namedtuple
import re
import numpy as np

Line = namedtuple('Line', ['num', 'text', 'time'])

# TODO:
# - DEAL WITH DOCSTRINGS

def _indent(line):
	return (len(line) - len(line.lstrip('\t')))


def _match_indent(line1, line2):
	"""Modify line2 to match line1's indent"""
	ntabs = _indent(line1)
	return '\t' * ntabs + line2


def skip_line(line:str):
	if line.lstrip().startswith(('for ', 'while ', 'if ', 'else:', 'elif ', 'return ', 'def ')):
		return True
	if line.strip() == '':
		return True

	# comment
	if line.lstrip().startswith('#'):
		return True

	return False

def parse_time(s):
	"""Given time in seconds, return order of magnitude which gives the time as a unit between 1-1000"""
	if s == 0:
		return '000  s'
	oom = np.log10(s)//3
	oom_lookup = {-3:'ns', -2: 'us', -1: 'ms', 0: 's'}

	v = s * 10**(-3 * oom)
	return f'{int(v):03d} {oom_lookup[oom]}'

class Timer():
	def __init__(self):
		self.times = {}
		self.t0 = perf_counter()

	def __call__(self, line):
		self.times[line] = perf_counter() - self.t0
		self.t0 = perf_counter()


class MultilineHandler:
	"""Handle multi-line expressions by tracking opening brackets"""
	def __init__(self):
		self.is_active = False
		self.stack = []

	def check_line(self, line):
		line_stack = []
		pairs = {"{": "}", "(": ")", "[": "]"}

		# add all brackets in line to stack, removing pairs
		for c in line:
			if c in "{[(":
				line_stack.append(c)
			if c in '}])':
				if line_stack and c == pairs[line_stack[-1]]:
					line_stack.pop()
				else:
					line_stack.append(c) # add to stack, hopefully to be considered with other lines

		if line_stack:
			self.stack += line_stack
			self.is_active = True

		self.resolve_stack() # resolve current stack in case multiline ends here

	def resolve_stack(self):

		# go through current stack, resolving found pairs if any
		string_stack = ''.join(self.stack)
		pairs = '()', '[]', '{}'
		while any(p in string_stack for p in pairs):
			for p in pairs:
				string_stack = string_stack.replace(p, '')

		# if stack is empty, multiline is over
		if not string_stack:
			self.is_active = False

		self.stack = [*string_stack]

	def balanced(self, line):
		"""Return True if line has balanced brackets"""
		return line.count('(') == line.count(')') and line.count('[') == line.count(']') and line.count('{') == line.count('}')

	def __bool__(self):
		return self.is_active

def write_html(lines: [Line], out_file='out.html',
			   col_min = (255, 255, 255), col_max = (255, 0, 0)):
	"""Given a dict of line_num:line_text, and of line_num:exec time,
	produce an html file with the lines coloured by execution time"""

	times = [l.time for l in lines]

	html = '<body>'
	html += f'<p>Elapsed: {parse_time(sum(times))}</p>'
	html += '<table style="border-spacing:0px";>'

	vmin, vmax = min(times), max(times)
	col_min, col_max = np.array(col_min), np.array(col_max)

	for line in lines:
		rval = (line.time - vmin) / (vmax - vmin)
		col = col_min + (col_max - col_min) * rval
		backghex = ''.join(f'{int(i):0{2}x}' for i in col)

		elapsed = parse_time(line.time).replace(' ', '&nbsp;')
		l = line.text.replace('\t', '&emsp;&emsp;&emsp;&emsp;')

		html_row = f'<tr style="background-color:#{backghex}">'
		html_row += f'<td> <tt>{line.num:03d}<tt> </td>'
		html_row += f'<td> <tt>[{elapsed}]<tt> </td>'
		html_row += f'<td> <tt>{l}<tt> </td>'
		html_row += '</tr>'
		html += '\n' + html_row

	html += '\n</table></body>'

	with open(out_file, 'w') as outfile:
		outfile.write(html)

def profile_func(func,  out_file='out.html'):
	def wrapper(*args, **kwargs):

		lines, line_start = inspect.getsourcelines(func)
		# line_start = where @ is

		def_line = lines[1]
		mod_def_line = def_line.replace(f'def {func.__name__}', 'def profiled_func')
		base_indent = _indent(def_line)
		out_lines = [mod_def_line.lstrip('\t').rstrip()]

		mlh = MultilineHandler() # to handle code that spans multiple lines


		for n, line in enumerate(lines[2:-1]):
			line = line[base_indent:].rstrip()
			mlh.check_line(line)

			_output_line = line
			if not mlh.is_active and not skip_line(line):
				_output_line += f'; __timer({line_start + n + 2})'

			out_lines.append(_output_line)

		timer = Timer()
		scope = {'perf_counter': perf_counter, '__timer': timer, **globals(), **locals()}
		print('\n'.join(out_lines))
		exec('\n'.join(out_lines), scope)
		res = scope['profiled_func'](*args, **kwargs)

		line_results = []
		for n, line in enumerate(lines[1:-1]):
			line_num = line_start + n + 1
			l = Line(line_num, line, timer.times.get(line_num, 0))
			line_results.append(l)

		write_html(line_results, out_file=out_file)

		return res

	return wrapper