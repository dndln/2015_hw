import numpy as np
import ipdb
import timeit

def simulate_prizedoor(nsim):
    array = [0, 1, 2]
    return np.random.choice(array, size=nsim)

def simulate_guess(nsim):
    return simulate_prizedoor(nsim)

def goat_door(prizedoors, guesses):
    out_list = []
    for curr_tuple in zip(prizedoors, guesses):
        possible_set = {0, 1, 2} - set(curr_tuple)
        out_list.append(np.random.choice(list(possible_set)))
    return np.array(out_list)

def switch_guess(guesses, goatdoors):
    out_list = []
    for curr_tuple in zip(guesses, goatdoors):
        # assuming goatdoor is never the same as guess,
        # this will be a one-element set
        possible_set = {0, 1, 2} - set(curr_tuple)
        out_list.append(next(iter(possible_set)))
    return np.array(out_list)

# a "cooler" way to do switch_guess... but is it faster?
def switch_guess_2(guesses, goatdoors):
    possible_set_array = np.repeat({0, 1, 2}, len(guesses))
    set_array = possible_set_array - np.array(
        [set(curr_tuple) for curr_tuple in zip(guesses, goatdoors)])
    out_array = np.array([next(iter(x)) for x in set_array])
    return out_array

def win_percentage(guesses, prizedoors):
    bool_array = np.equal(guesses, prizedoors)
    # naughtily cast True/False to 1/0 when taking mean
    percentage = bool_array.mean() * 100
    return percentage

def monty_hall(n):
    print('='*32)
    print('Simulating keeping the original guess with {} games'.format(n))
    guesses = simulate_guess(n)
    prizedoors = simulate_prizedoor(n)
    # not needed since he's not changing the door
    goatdoors = goat_door(prizedoors, guesses)
    percentage = win_percentage(guesses, prizedoors)
    print('Win percentage was {:.7}%.'.format(percentage))

    print('Simulating switching doors with {} games'.format(n))
    guesses = simulate_guess(n)
    prizedoors = simulate_prizedoor(n)
    goatdoors = goat_door(prizedoors, guesses)
    new_guesses = switch_guess(guesses, goatdoors)
    percentage = win_percentage(new_guesses, prizedoors)
    print('Win percentage was {:.7}%.'.format(percentage))


if __name__ == '__main__':
    # guesses = simulate_guess(100000)
    # prizedoors = simulate_prizedoor(100000)
    # goatdoors = goat_door(prizedoors, guesses)
    #
    # # need lambda to make the function a callable,
    # # or it'll just be evaluated and become an array
    # t1 = timeit.Timer(lambda: switch_guess(guesses, goatdoors))
    # time1 = t1.timeit(number=100)
    # t2 = timeit.Timer(lambda: switch_guess_2(guesses, goatdoors))
    # time2 = t2.timeit(number=100)
    # # ipdb> time1
    # # 19.6355751559895
    # # ipdb> time2
    # # 19.958219507010654
    # # switch_guess is the winner by a hair! (maybe I had too many np.arrays() in
    # # switch_guess_2().)
    for i in range(50):
        monty_hall(10000)
    # ipdb.set_trace()

    # matplotlib legend positions
    # right
	# center left
	# upper right
	# lower right
	# best
	# center
	# lower left
	# center right
	# upper left
	# upper center
	# lower center
