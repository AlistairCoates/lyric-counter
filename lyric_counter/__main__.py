import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('artist', type=str, help='The artist name')
    args = parser.parse_args()


if __name__ == '__main__':
   main()
