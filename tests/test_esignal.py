import unittest
from slipstream.data import ESignalCSV
import zipfile
import os
from tempfile import TemporaryDirectory
import time
from time import clock_gettime_ns


class MyTestCase(unittest.TestCase):
    def test_esignal_read_csv(self):
        zip_path, _ = os.path.split(os.path.abspath(__file__))
        zip_path = os.path.join(zip_path, "VX_spread.csv.zip")
        assert os.path.exists(zip_path)
        with TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmp_dir)
                extracted_files = os.listdir(tmp_dir)
                assert len(extracted_files) > 0
                csv_files = [filename for filename in extracted_files if filename.endswith(".csv")]
                begin = clock_gettime_ns(time.CLOCK_UPTIME_RAW)
                df = ESignalCSV(os.path.join(tmp_dir, csv_files[0])).get_dataframe()
                raw_read_elapsed = clock_gettime_ns(time.CLOCK_UPTIME_RAW) - begin
                print(f"raw read elapsed={raw_read_elapsed}")
                self.assertTrue("Timestamp" in df.columns)

                # Load CSV again. This time there should be a parquet cache, so it should be much faster
                begin = clock_gettime_ns(time.CLOCK_UPTIME_RAW)
                df2 = ESignalCSV(os.path.join(tmp_dir, csv_files[0])).get_dataframe()
                cache_read_elapsed = clock_gettime_ns(time.CLOCK_UPTIME_RAW) - begin
                print(f"cache read elapsed={cache_read_elapsed}")
                read_times_mult = raw_read_elapsed * 1.0 / cache_read_elapsed
                print(f"mult={read_times_mult}")
                self.assertTrue(read_times_mult > 500)


if __name__ == '__main__':
    unittest.main()
