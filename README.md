## Semanticflow-extraction

The project extract an educational knowledge graph from a given coursera course by scarping materials from Coursera and then
extracting coruse elements and their relation from the content.

```
python src/extractor.py --domain mathematics --data data/sample_courses/linear_algebra/ --url https://www.coursera.org/learn/single-variable-calculus
```

The output of the extractor are a json file that will be
saved under the path provided by data. The json file has the following format

```
{
  "course_id": "course_identifier",
  "domain_type": "mathematics|programming|humanities",
  "course_title": "...",
  "modules": [
    {
      "module_id": "m1",
      "title": "...",
      "lessons": [
        {
          "lesson_id": "l1",
          "title": "...",
          "scale": "lesson",
          "text"
    }
  ],
  "cross_scale_links": [
    {
      "lesson_node": "n1",
      "module_node": "mn2",
      "relationship": "part_of"
    }
  ]
}
```


