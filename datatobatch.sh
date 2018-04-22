
for dtype in 'train' 'valid' 'test'
do
	#paste -d' ' < example/$dtype.data - - > tmp.tsv
	python embedH5.py Jariddata/$dtype.fa Jariddata/$dtype.target Jaridexp/$dtype.h5
done