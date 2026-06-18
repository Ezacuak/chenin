from report import Report


def main():
    r13 = Report("./data/NOI_S/NOI_S_13.txt")

    for k in r13:
        print(r13[k])


if __name__ == "__main__":
    main()
