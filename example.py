from pfhm import profile_func

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


if __name__ == '__main__':
	func(0)
