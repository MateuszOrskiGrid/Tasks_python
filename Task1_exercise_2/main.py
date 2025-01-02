"""
Exercise 2 task 1
"""
numbers = [4, 7, 2, 8, 4, 7, 10, 2]

#set for removing duplicates
unique_numbers = tuple(set(numbers))

min_number = min(unique_numbers)
max_number = max(unique_numbers)

print("Tuple of unique numbers:", unique_numbers)
print("Minimum number:", min_number)
print("Maximum number:", max_number)
