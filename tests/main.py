def pick_items(my_list):
    if len(my_list) <= 4:
        return my_list[:4]
    else:
        return my_list[:2] + my_list[-2:]


# test
my_array = [1, 2, 3, 4]
result = pick_items(my_array)
print(result)
