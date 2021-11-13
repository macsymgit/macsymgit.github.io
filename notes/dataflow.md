- [Dataflow](#dataflow)
	- [Apache Beam](#apache-beam)
		- [Element-wise tranformation](#element-wise-tranformation)
			- [MapElements (1 to 1 mapping)](#mapelements-1-to-1-mapping)
			- [ParDo (1 to 1 or less mapping)](#pardo-1-to-1-or-less-mapping)
			- [Filters](#filters)
			- [Flatten (Union)](#flatten-union)
			- [Partition (to multu PCollection)](#partition-to-multu-pcollection)
			- [Side Inputs (join by key)](#side-inputs-join-by-key)
		- [Aggregation tranformation](#aggregation-tranformation)
			- [Distinct](#distinct)
			- [Count](#count)
			- [GroupByKey](#groupbykey)
		- [Join](#join)
			- [Inner Join](#inner-join)
			- [Left Join](#left-join)
			- [Right Join](#right-join)

# Dataflow

## Apache Beam

### Element-wise tranformation

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
PCollectionList<String> list=PCollectionList.of(pCustList1)
    .and(pCustList2).and(pCustList3);
    
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
PCollection<KV<String,String>> pSideInput = p.apply(TextIO...))
    .apply(ParDo.of(new DoFn<String, KV<String,String>>() {

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
### Aggregation tranformation

#### Distinct
- Use Distinct.<String>create() get new distinct PCollection 
```java
PCollection<String> uniqueCust=pCustList.apply(Distinct.<String>create());
```  
#### Count
- Count.globally() counts the number of elements in the entire PCollection. The result is a collection with a single element.
- Count.perKey() counts how many elements are associated with each key. It ignores the values. The resulting collection has one output for every key in the input collection.
- Count.perElement() counts how many times each element appears in the input collection. The output collection is a key-value pair, containing each unique element and the number of times it appeared in the original collection.

```java
		PCollection<Long> pLong = pInput.apply(Count.globally());
		pLong.apply(ParDo.of(new DoFn<Long, Void>() {
			@ProcessElement
			public void processElement(ProcessContext c) {
				System.out.println(c.element());
			}
		}));
```

#### GroupByKey

1. PCollection convert as KV<String,String> by @ProcessElement function
2. Apply groupByKey and build KV<String,Iterable<Integer>>  (key and value to sum)
3. Convert KV<String,Iterable<Integer>> to output string

```java
//1 return PCollection as KV<String,String>
Pipeline p = Pipeline.create();
PCollection<KV<String,String>> pSideInput = p.apply(TextIO...))
    .apply(ParDo.of(new DoFn<String, KV<String,String>>() {

	@ProcessElement
	public void process(ProcessContext c) {
		Strring arr[]  = c.element().split(",");
		//arr[0] as key and arr[1] as value to map
		c.output(KV.of(arr[0],arr[1]));
	}
}));

//2 Apply groupByKey 
PCollection<KV<String,Iterable<Integer>>> pIterable = pSideInput.apply(GroupByKey.<String, Integer>create());

//3 Convert KV<String,Iterable<Integer>> to output string
PCollection<String> output = pIterable.apply(ParDo.of(new DoFn<KV<String, Iterable<Integer>>,String>() {

	@ProcessElement
	public void process(ProcessContext c) {
		String strKey=c.element().getKey();
		Iterable<Integer> vals=c.element().getValue();
		
		Integer sum=0;
		for (Integer integer : vals) {sum=sum+integer;}
		
		c.output(strKey+","+sum.toString());
	}
}));
```
### Join

#### Inner Join

1. 2 input PCollection convert as KV<String,String> by @ProcessElement function
2. Create TupleTag object.
3. Combine data sets using CoGroupByKey
4. Iterate CoGbkResult and build String  

```java
//1 input PCollection convert as KV check GroupBy example code

//2 Create TupleTag object.
		final TupleTag<String> orderTuple = new TupleTag<String>();
		final TupleTag<String> userTuple = new TupleTag<String>();

//3 Combine data sets using CoGroupByKey
		PCollection<KV<String, CoGbkResult>> result = KeyedPCollectionTuple.of(orderTuple, pOrderCollection)
						.and(userTuple, pUserCollection)
						.apply(CoGroupByKey.<String>create());

//4 Iterate CoGbkResult and build output String  
		PCollection<String> output = result.apply(ParDo.of(new DoFn<KV<String, CoGbkResult>, String>() {
				
			@ProcessElement
			  public void processElement(ProcessContext c) {
			   	    	
					String strKey = c.element().getKey();
					CoGbkResult valObject = c.element().getValue();
					
					Iterable<String> orderTable= valObject.getAll(orderTuple);
					Iterable<String> userTable = valObject.getAll(userTuple);
					
					for (String order : orderTable) {
						for (String user : userTable) {							
							c.output(strKey+","+order+","+user);
						}
					}
			  }
		}));
```

#### Left Join

4. first 3 steps same as inner join, only Iterate CoGbkResult right PCollection first check with hasnext() for Left PCollection

```java
					for (String order : orderTable) { //orderTable as right Pcollection
						if(userTable.iterator().hasNext()) {
							for (String user : userTable) {							
								c.output(strKey+","+order+","+user);
							}
						} else {
							c.output(strKey+","+order+","+null);
						}
					}
```

#### Right Join

4. first 3 steps same as inner join, only Iterate CoGbkResult left PCollection first check with hasnext() for Right PCollection

```java
					for (String user : userTable) { //orderTable as right Pcollection
						if(orderTable.iterator().hasNext()) {
							for (String order : orderTable) {							
								c.output(strKey+","+user+","+order);
							}
						} else {
							c.output(strKey+","+user+",null,null,null");
						}
					}
```