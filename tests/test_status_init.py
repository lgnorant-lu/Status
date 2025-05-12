# tests/test_status_init.py
import unittest

class TestStatusPackageInit(unittest.TestCase):

    def test_import_status_package(self):
        """
        Test that the main 'status' package can be imported without errors.
        测试主'status'包可以无错误地导入。
        """
        try:
            import status
        except ImportError as e:
            self.fail(f"Failed to import 'status' package: {e}")
        except Exception as e:
            self.fail(f"An unexpected error occurred during 'status' package import: {e}")
        self.assertTrue(True, "'status' package imported successfully.")

if __name__ == '__main__':
    unittest.main() 