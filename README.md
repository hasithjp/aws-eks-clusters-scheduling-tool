AWS EKS Scheduling Tool
=======

This is application is implemented using an open source tool called [H2O Wave](https://wave.h2o.ai/) by [H2O.ai](https://h2o.ai/). 
This app is built to manage bulk EKS clusters across all the enabled regions in AWS root account from one place and it 
enables us to stop/start clusters on demand and set/remove scheduled actions to stop clusters on weekends 
automatically based on the given timezone. Furthermore, the app will show the existing scheduled actions if available 
and the original cluster size will not be changed during the functions in the app.

### Available Functions
- Can list all the EKS clusters in all the enabled regions in Root account despite the Project tag
- Can list the clusters based on the selected Project and Region
- Can group/filter the cluster table with any parameter as required
- Users can stop/start clusters on demand
- Users can set/remove Stop On Weekends scheduling action to stop clusters automatically during the weekends based on the selected timezone
- Users can start the cluster during weekends if required by removing the Stop On Weekends schedule
- User can see the cost details of the cluster and approx. cost savings can be made with Stop on Weekend schedule
- Users can filter the cluster table to check running/stopped clusters, clusters to be stopped on weekends etc

### Pre-requisites
- Export the AWS Access keys to the environment. Or set them as env variables
- To filter clusters based on projects, Add `Project` tag to EKS clusters and Replace the `_PROJECT#_` values in the scripts,
Otherwise you can use choose `All` without filtering based on the project
- Add the required regions to `aws_functions.py` for the `enabledRegions` variable

![195410216-b4ae11be-832f-448e-bf74-5001518ff804](https://user-images.githubusercontent.com/39459414/218305776-8089b677-5206-4e26-acd3-756bbb68059c.png)
![195410210-ecd33d8e-79fb-4708-aef5-78af900d85e2](https://user-images.githubusercontent.com/39459414/218305904-f5d33181-70f0-45d2-9813-50ae48864d9f.png)
![195410199-e9184a68-06c8-46b8-b6d5-ad8aee563d58 (1)](https://user-images.githubusercontent.com/39459414/218305785-55245f02-d75a-479e-8d39-38e390b6a82b.png)

