# Dataflow

## Apache Beam

### Transformation

#### MapElements (1 to 1 mapping)
- Class extends SimpleFunction and implements apply
- Lambda apply

#### ParDo (1 to 1 or less mapping)
- Class extends DoFn with @ProcessElement function
- Embaded ParDo with @ProcessElement function

#### Filters 
- Class extends SerializableFunction implements apply return Boolean

```java
class MyFilter implements SerializableFunction<String, Boolean>{
	@Override
	public Boolean apply(String input) {
		return input.contains("Los Angeles");
	}
}
```

#### Flatten (Union)
- Use PCollectionList and Flatten

```java
PCollectionList<String> list=PCollectionList.of(pCustList1).and(pCustList2).and(pCustList3);
PCollection<String> merged=list.apply(Flatten.pCollections());
```

#### Partition (to multu PCollection)
- Use Partition.of and PartitionFn function
```java
// Split students up into 10 partitions, by percentile:
PCollectionList<Student> studentsByPercentile =
    students.apply(Partition.of(10, new PartitionFn<Student>() {
        public int partitionFor(Student student, int numPartitions) {
            return student.getPercentile()  // 0..99
                 * numPartitions / 100;
        }}));
```

#### Side Inputs (join by key)
1. PCollection return as KV<String,String> by @ProcessElement function
2. Convert step 1 to PCollectionView
3. Use withSideInput to get a Map and join by key

```java
//1 return PCollection as KV<String,String>
Pipeline p = Pipeline.create();
PCollection<KV<String,String>> pSideInput = p.apply(TextIO...)).apply(ParDo.of(new DoFn<String, KV<String,String>>() {

	@ProcessElement
	public void process(ProcessContext c) {
		Strring arr[]  = c.element().split(",");
		//arr[0] as key and arr[1] as value to map
		c.output(KV.of(arr[0],arr[1]));
	}
}));

//2 to PCollectionView
PCollectionView<Map<String, String>> pMap = pSideInput.apply(View.asMap());

//3 Use withSideInput to get a Map and join by key 
PCollection<String> pMain = p.apply(TextIO...));

pMain.apply(Pardo.of(new DoFn<String,String>() {
	@ProcessElement
	public void process(ProcessContext c) {
        Map<String, String> psideInputView = c.sideInput(pMap);
        String arr[]  = c.element().split(",");
        String key = arr[0];
        String sideInputValue = psideInputView.get(key);
        c.output(c.element()+","+sideInputValue);
    }

}).withSideInput(pMap));
```

### Aggregation Functions

#### Distinct

#### Count

#### GroupByKey

