import os

def create_test_bins():
    # File 1: A pattern of 0xAA with a hidden message
    data1 = bytearray([0xAA] * 1024)
    data1[512:523] = b"SECRET_ONE"
    
    # File 2: A pattern of 0xBB with a different hidden message
    data2 = bytearray([0xBB] * 1024)
    data2[512:523] = b"SECRET_TWO"
    
    with open("test1.bin", "wb") as f:
        f.write(data1)
    with open("test2.bin", "wb") as f:
        f.write(data2)
    
    print("Files created: test1.bin and test2.bin (1KB each)")

if __name__ == "__main__":
    create_test_bins()
