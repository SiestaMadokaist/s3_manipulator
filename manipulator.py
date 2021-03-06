import boto3
import json
import re
import os

S3 = boto3.resource("s3")

Guesser = {
	".jpg": "image/jpeg",
	".png": "image/png",
	".gif": "image/gif",
	".bmp": "image/bmp",
	".tiff": "image/tiff",
	".txt": "text/plain",
	".rtf": "text/rtf",
	".html": "text/html",
	".css": "text/css",
	".mp3": "audio/mp3",
	".zip": "application/zip",
	".js": "application/x-javascript",
	".json": "application/json",
	".gz": "application/x-gzip",
	".mp4": "video/mp4",
	".xml": "text/xml"
}
class S3Manipulator:
	DefaultRejectRegex = ()
	DefaultFilterRegex = ()

	@staticmethod
	def guess_content_type(item):
		regex = re.compile(r"\.\w+$")
		try:
			extension = regex.search(item).group();
		except AttributeError:
			pass
		else:
			return Guesser.get(extension, "text/plain")

	def __init__(
		self,
		local_root=".",
		filter_regexs=DefaultFilterRegex,
		reject_regexs=DefaultRejectRegex,
	):
		self.root = local_root
		assert len(filter_regexs) > 0, "filter_regexs can't be empty"
		self.filter_regexs = self.regex_compile(filter_regexs)
		self.reject_regexs = self.regex_compile(reject_regexs)

	def regex_compile(self, items):
		return [re.compile(item) if type(item) == str else item for item in items]

	def reject(self, *reject_item):
		reject_regexs = self.regex_compile(reject_item)
		return S3Manipulator(self.root, self.filter_regexs, self.reject_regexs + reject_regexs)

	def filter(self, *filter_item):
		filter_regexs = self.regex_compile(filter_item)
		return S3Manipulator(self.root, self.filter_regexs + filter_regexs, self.reject_regexs)

	@property
	def items(self):
		def file_generator(path):
			filter_regexs = self.filter_regexs
			reject_regexs = self.reject_regexs
			for root, fos, fis in os.walk(path):
				for fi in fis:
					fname = "{root}/{fi}".format(**vars())
					passed_filter = any(regex.search(fname) is not None for regex in filter_regexs)
					passed_reject = all(regex.search(fname) is None for regex in reject_regexs)
					if(passed_filter and passed_reject):
						yield fname
		return list(file_generator(self.root))

	def upload_to(self, bucket_name, path_formatter=None, silent=False, **kwargs):
		_path_formatter = S3Manipulator.default_path_formatter if path_formatter is None else path_formatter
		if(not silent):
			return self._noisy_upload(bucket_name, _path_formatter, **kwargs)
		else:
			bucket = S3.Bucket(bucket_name)
			for item in self.items:
				bucket.put_object(Body=open(item), Key=_path_formatter(item), ContentType=S3Manipulator.guess_content_type(item));

	def _noisy_upload(self, bucket_name, path_formatter, **kwargs):
		bucket = S3.Bucket(bucket_name)
		for i, item in enumerate(self.items):
			body = open(item, 'rb')
			key = path_formatter(item)
			print("{} => {}".format(body, key))
			s3obj = bucket.put_object(Body=body, Key=key, ContentType=S3Manipulator.guess_content_type(item), **kwargs)

	def default_path_formatter(item):
		return re.sub(r"^\./", "", item)


def main():
	manipulator = S3Manipulator()
	# manipulator = S3Manipulator(filter_regexs=[".js$", ".css$", ".txt$"]).filter(".py$").reject("uploader").reject("req")
	manipulator.upload_to("ramadoka.mivo.cf")


if __name__ == '__main__':
	main()
