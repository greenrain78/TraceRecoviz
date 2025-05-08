from src.parser.utils.extract import extract_callee

data_list =[
    "virtual int OnTheFlyPrimeTable::GetNextPrime(int) const (arg0=[type: int] 0)"
]
for raw in data_list:
    print(extract_callee(data_list))