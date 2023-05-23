# pfhm (Python Function HeatMap tool)

Mini line-by-line timing tool made for debugging functions in Python.

This is not designed to be used as a large scale profiling tool - rather as a quick debugging of small functions.

## Usage

Install via `python setup.py install`.

See `example.py` for a full example.

Either use as a decorator,

```python
from profiler import profile_func
@profile_func()
def func(*args, **kwargs):
	...
```

Where the output will be written to `out.html`, or inline,

`profile_func(func, out_file='custom_location.html')(*args, **kwargs)`.

## Example

As in `example.py`, we call the function

```python
@profile_func
def func(x):
	list = []
	for i in range(100):
		x += 2
		list.append([4] * 500)
		x += 3
		list.append([4] * 10000)
		x += 7
	return x
```

And receive the output:

<body><p>Elapsed: 002 ms</p><table style="border-spacing:0px";><th>Line</th><th>Calls</th><th>Elapsed</th><th>Code</th>
<tr style="background-color:#ffffff"><td> <code>004<code> </td><td> <code>[0]<code> </td><td> <code>[000&nbsp;&nbsp;s]<code> </td><td> <code>def func(x):
<code> </td></tr>
<tr style="background-color:#fff2f2"><td> <code>005<code> </td><td> <code>[1]<code> </td><td> <code>[078&nbsp;us]<code> </td><td> <code>&emsp;&emsp;&emsp;&emsp;list = []
<code> </td></tr>
<tr style="background-color:#fff7f7"><td> <code>006<code> </td><td> <code>[100]<code> </td><td> <code>[047&nbsp;us]<code> </td><td> <code>&emsp;&emsp;&emsp;&emsp;for i in range(100):
<code> </td></tr>
<tr style="background-color:#fff7f7"><td> <code>007<code> </td><td> <code>[100]<code> </td><td> <code>[045&nbsp;us]<code> </td><td> <code>&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;x += 2
<code> </td></tr>
<tr style="background-color:#ffe7e7"><td> <code>008<code> </td><td> <code>[100]<code> </td><td> <code>[152&nbsp;us]<code> </td><td> <code>&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;list.append([4] * 500)
<code> </td></tr>
<tr style="background-color:#fff7f7"><td> <code>009<code> </td><td> <code>[100]<code> </td><td> <code>[045&nbsp;us]<code> </td><td> <code>&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;x += 3
<code> </td></tr>
<tr style="background-color:#ff0000"><td> <code>010<code> </td><td> <code>[100]<code> </td><td> <code>[001&nbsp;ms]<code> </td><td> <code>&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;list.append([4] * 10000)
<code> </td></tr>
<tr style="background-color:#ffdddd"><td> <code>011<code> </td><td> <code>[100]<code> </td><td> <code>[212&nbsp;us]<code> </td><td> <code>&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;x += 7
<code> </td></tr>
</table></body>

