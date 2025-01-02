"""
Script for exercise 1 task 1
"""
def get_file_extension(file_name):
    """
    Function for getting file name and getting its extension
    """
    try:
        if '.' in file_name and file_name.rsplit('.', 1)[1]:
            extension = file_name.rsplit('.', 1)[1]
            print(f"File extension: {extension}")
        else:
            raise ValueError("No extension found in the file name.")
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    input_file_name = input("Enter the file name: ")
    get_file_extension(input_file_name)
