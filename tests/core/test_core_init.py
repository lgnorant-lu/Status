# tests/core/test_core_init.py
import unittest

class TestCorePackageInit(unittest.TestCase):

    def test_import_core_package(self):
        """
        Test that the 'status.core' package can be imported without errors.
        测试 'status.core' 包可以无错误地导入。
        """
        try:
            import status.core
        except ImportError as e:
            self.fail(f"Failed to import 'status.core' package: {e}")
        except Exception as e:
            self.fail(f"An unexpected error occurred during 'status.core' package import: {e}")
        self.assertTrue(True, "'status.core' package imported successfully.")

if __name__ == '__main__':
    unittest.main() 