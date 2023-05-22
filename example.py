from profiler import profile_func


@profile_func
def func(x=0):
	for i in range(100):
		x += 2
		[].append([4]*500)
		x += 3
		[].append([4] * 1000)
		x += 7
	return x


if __name__ == '__main__':
	func(0)
