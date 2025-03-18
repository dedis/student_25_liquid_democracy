a = 1
b = 1
c = 1

for i in range(20):
    temp_a = a
    temp_b = b
    temp_c = c

    a = temp_b
    b = 0.5 * temp_a
    c = 0.5 * temp_a + temp_c

    print(f"i: {i}, a: {a}, b: {b}, c: {c}, sum: {a + b + c}")