# 1. Ask the user for the first number
# int() tells the computer this is a number, not just text
x = int(input("Enter number for x: "))

# 2. Ask the user for the second number
y = int(input("Enter number for y: "))

# 3. Show what is in the boxes right now
print("Before swap: x =", x, "and y =", y)

# 4. The Magic Swap Line
# This moves the value of y into x, and x into y at the same time!
x, y = y, x

# 5. Show the boxes after the swap
print("After swap:  x =", x, "and y =", y)