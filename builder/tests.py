import requests
from django.test import TestCase
import time


thumbor_ip = "localhost:8081"
imagor_ip = "localhost:8000"


def thumbor_upscale_fillwhite_test():
    image_test = "https://i.redd.it/c3uhsgo1vx541.jpg"
    url = f"http://{thumbor_ip}/unsafe/fit-in/350x350/filters:upscale():fill(white)/{image_test}"
    requests.get(url)


def imagor_upscale_fillwhite_test():
    image_test = "https://i.redd.it/c3uhsgo1vx541.jpg"
    url = f"http://{imagor_ip}/unsafe/fit-in/350x350/filters:upscale():fill(white)/{image_test}"
    requests.get(url)


def thumbor_trasform_test():
    image_test = "https://i.redd.it/c3uhsgo1vx541.jpg"
    url = f"http://{thumbor_ip}/unsafe/fit-in/1200x/{image_test}"
    requests.get(url)


def imagor_trasform_test():
    image_test = "https://i.redd.it/c3uhsgo1vx541.jpg"
    url = f"http://{imagor_ip}/unsafe/fit-in/1200x/{image_test}"
    requests.get(url)


if __name__ == "__main__":
    start_time = time.time()
    thumbor_upscale_fillwhite_test()
    print("--- %s seconds ---" % (time.time() - start_time))

    start_time = time.time()
    imagor_upscale_fillwhite_test()
    print("--- %s seconds ---" % (time.time() - start_time))

    start_time = time.time()
    thumbor_trasform_test()
    print("--- %s seconds ---" % (time.time() - start_time))

    start_time = time.time()
    imagor_trasform_test()
    print("--- %s seconds ---" % (time.time() - start_time))
