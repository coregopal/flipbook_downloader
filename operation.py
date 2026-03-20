# 1. Ask the user for a number
# float() lets us use decimals (like 10.5) instead of just whole numbers
num = float(input("Enter a number to do some math: "))

# 2. Calculate the Square and Cube
# Square is number * number
square = num ** 2
# Cube is number * number * number
cube = num ** 3

# 3. Calculate the Roots (The "Opposites")
# Square root is the same as the power of 1/2 (0.5)
sqrt = num ** 0.5
# Cube root is the same as the power of 1/3
croot = num ** (1/3)

# 4. Show the results
print("Square:", square)
print("Cube:", cube)
print("Square Root:", sqrt)
print("Cube Root:", croot)