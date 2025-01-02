"""
exercise 4 task 1
"""
if __name__ == "__main__":
    while True:
        zdanie = input("Podaj zdanie:")
        zmienna=isinstance(zdanie, str)
        if zmienna == 1:
            break
    print(f"{zdanie}\n")

    slownik={}
    for x in zdanie:
        if x in slownik:
            slownik[x] = slownik[x] + 1
        else:
            slownik[x] = 1
    print(slownik)
# End-of-file (EOF)
