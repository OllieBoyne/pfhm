import numpy as np
import inspect
from time import perf_counter
from collections import defaultdict, namedtuple
from typing import List
import re

loops_and_conditionals = ('for ', 'while ', 'if ', 'else:', 'elif ')
Line = namedtuple('Line', ['num', 'text', 'num_calls', 'total_elapsed'])

def _indent(line):
	return (len(line) - len(line.lstrip('\t')))


def _match_indent(line1, line2):
	"""Modify line2 to match line1's indent"""
	ntabs = _indent(line1)
	return '\t' * ntabs + line2


def skip_line(line:str):
	if line.lstrip().startswith(('return ', 'def ')):
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
	def __init__(self, callable=None):
		"""
		:param callable: function to call on each line
		"""
		self.times = defaultdict(list)
		self.t0 = perf_counter()
		self.callable = callable

	def __call__(self, line):
		if self.callable is not None:
			self.callable()

		self.times[line].append(perf_counter() - self.t0)
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
				if line_stack and c == pairs.get(line_stack[-1],False):
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

def write_html(lines: List[Line], out_file='out.html',
			   col_min = (255, 255, 255), col_max = (255, 0, 0)):
	"""Given a dict of line_num:line_text, and of line_num:exec time,
	produce an html file with the lines coloured by execution time"""

	times = [l.total_elapsed for l in lines]

	html = '<body>'
	html += f'<p>Elapsed: {parse_time(sum(times))}</p>'
	html += '<table style="border-spacing:0px";>'
	html += '<th>Line</th><th>Calls</th><th>Elapsed</th><th>Code</th>'

	vmin, vmax = min(times), max(times)
	col_min, col_max = np.array(col_min), np.array(col_max)

	for line in lines:
		if vmin == vmax == 0:
			rval = 0
		else:
			rval = (line.total_elapsed - vmin) / (vmax - vmin)

		col = col_min + (col_max - col_min) * rval
		backghex = ''.join(f'{int(i):0{2}x}' for i in col)

		elapsed = parse_time(line.total_elapsed).replace(' ', '&nbsp;')
		l = line.text.replace('\t', '&emsp;&emsp;&emsp;&emsp;')

		html_row = f'<tr style="background-color:#{backghex}">'
		html_row += f'<td> <code>{line.num:03d}<code> </td>'
		html_row += f'<td> <code>[{line.num_calls}]<code> </td>'
		html_row += f'<td> <code>[{elapsed}]<code> </td>'
		html_row += f'<td> <code>{l}<code> </td>'
		html_row += '</tr>'
		html += '\n' + html_row

	html += '\n</table></body>'

	with open(out_file, 'w') as outfile:
		outfile.write(html)

def split_function(func):
	"""Returns an array of lines defining the signature,
	and an array of lines defining the function.
	Removes docstring. Removes decorators"""
	func_text = inspect.getsource(func)

	# start from def
	def_char = func_text.find('def ')

	# end of signature is where first ) : is on a single line (can be characters between them)
	signature_end_regex = re.compile(r'\)*.:\n')
	end_sig = signature_end_regex.search(func_text[def_char:]).end() + def_char

	# if docstring is present, get end of it (including up to the following \n)
	split_idx = end_sig
	if func.__doc__:
		doc_idx = func_text.find(func.__doc__) + len(func.__doc__)
		doc_idx = func_text.find('\n', doc_idx) + 1
		split_idx = doc_idx

	return func_text[def_char:end_sig].split("\n"), func_text[split_idx:].split("\n")

def profile_func(func,  out_file='out.html', debug=False, callable=None):
	def wrapper(*args, **kwargs):

		sig_lines, func_lines = split_function(func)

		sig_lines[0] = sig_lines[0].replace(f'def {func.__name__}', 'def profiled_func')
		base_indent = _indent(sig_lines[0])
		out_lines = [i.lstrip('\t').rstrip() for i in sig_lines]

		mlh = MultilineHandler() # to handle code that spans multiple lines

		for n, line in enumerate(func_lines):
			line = line[base_indent:].rstrip()
			mlh.check_line(line)

			_output_line = line

			timer_call = f'__timer({n})'

			if not mlh.is_active and not skip_line(line):
				if line.lstrip().startswith(loops_and_conditionals):
					# timer object must be on following line for eg if:
					_output_line += '\n\t' + _match_indent(line, timer_call)

				else:
					# timer object can be on same line
					_output_line += f'; {timer_call}'

			out_lines.append(_output_line)

		timer = Timer(callable=callable)
		scope = {'perf_counter': perf_counter, '__timer': timer, **globals(), **locals(),
				 **func.__globals__}

		if debug:
			print('\n'.join(out_lines))

		exec('\n'.join(out_lines), scope)
		res = scope['profiled_func'](*args, **kwargs)

		line_results = []
		for n, line in enumerate(sig_lines):
			line_num = n + 1
			l = Line(line_num, line, 1, 0)
			line_results.append(l)

		for m, line in enumerate(func_lines):
			line_num = n + m
			times = timer.times.get(m, [])
			l = Line(line_num, line, len(times), sum(times))
			line_results.append(l)

		write_html(line_results, out_file=out_file)

		return res

	return wrapper