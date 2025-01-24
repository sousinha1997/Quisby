import unittest
import os
from unittest.mock import patch
from pathlib import Path
from quisby.benchmarks.auto_hpl.extract import extract_auto_hpl_data
from quisby.benchmarks.linpack.extract import linpack_format_data

class TestAutoHPLExtract(unittest.TestCase):

    # Helper function to get the path for the sample data
    def get_sample_data_path(self, filename):
        return os.path.join(os.path.dirname(__file__), 'data', 'auto_hpl', filename)

    # Test when the file is correctly formatted
    @patch("quisby.benchmarks.auto_hpl.extract.linpack_format_data")
    def test_valid_file(self, mock_linpack_format_data):
        valid_file_path = self.get_sample_data_path("valid_data.csv")
        mock_linpack_format_data.return_value = [{"system": "TestSystem", "gflops": '4.8627e+02'}]
        system_name = "TestSystem"

        result = extract_auto_hpl_data(valid_file_path, system_name)
        mock_linpack_format_data.assert_called_with(
            results=[], system_name=system_name, gflops="4.8627e+02"
        )
        self.assertEqual(result, [{"system": "TestSystem", "gflops": "4.8627e+02"}])

    # Test when the file does not exist (FileNotFoundError)
    def test_file_not_found(self):
        invalid_file_path = "/path/to/nonexistent/file.csv"
        with self.assertRaises(FileNotFoundError):
            extract_auto_hpl_data(invalid_file_path, "TestSystem")

    # Test when the file does not have the correct extension (ValueError)
    def test_invalid_file_extension(self):
        invalid_file_path = self.get_sample_data_path("invalid_data.txt")  # A non-CSV file
        with self.assertRaises(ValueError):
            res = extract_auto_hpl_data(invalid_file_path, "TestSystem")

    # Test when the file has insufficient data (less than two lines)
    def test_insufficient_data(self):
        insufficient_data_file_path = self.get_sample_data_path("insufficient_data.csv")
        result = extract_auto_hpl_data(insufficient_data_file_path, "TestSystem")
        self.assertIsNone(result)
        no_data_file_path = self.get_sample_data_path("no_data.csv")
        with self.assertRaises(KeyError):
            result = extract_auto_hpl_data(no_data_file_path, "TestSystem")

    # Test when the Gflops field is missing (KeyError)
    def test_missing_gflops(self):
        missing_gflops_file_path = self.get_sample_data_path("missing_gflops.csv")
        with self.assertRaises(KeyError):
            extract_auto_hpl_data(missing_gflops_file_path, "TestSystem")

    # Test when there is a mismatch in header and data length (ValueError)
    def test_mismatched_header_and_data(self):
        mismatched_file_path = self.get_sample_data_path("mismatched_header_data.csv")
        with self.assertRaises(ValueError):
            extract_auto_hpl_data(mismatched_file_path, "TestSystem")

    # Test when there are permission issues with the file (PermissionError)
    def test_permission_error(self):
        permission_error_file_path = self.get_sample_data_path("permission_error_file.csv")
        # Mocking os.path.exists and open to simulate a PermissionError
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with self.assertRaises(PermissionError):
                extract_auto_hpl_data(permission_error_file_path, "TestSystem")

if __name__ == '__main__':
    unittest.main()
