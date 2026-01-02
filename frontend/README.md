# slotlist-frontend

## 📢 Project Status: Discontinued

After nearly a decade of serving the ArmA community, slotlist.online will be shut down on 31 December 2025. The project is no longer actively maintained due to time and resource constraints, and its underlying technology stack has become outdated. This repository remains available as an archive for historical and reference purposes. Thank you to everyone who contributed and supported the project over the years!

## Installation
### Requirements
* [Node](https://nodejs.org) 8.1 and up
* [Yarn](https://yarnpkg.com) 1.4 and up
* Webserver to serve generated static HTML/JS/CSS/images

#### Optional dependencies
* [Docker](https://www.docker.com/) 17.12 and up
* [Kubernetes](https://kubernetes.io/) 1.7 and up

### Setup
#### Install dependencies
```sh
$ yarn
```

#### Adjust required environment variables and config
Configuration will be transpiled into the frontend source code directly. All configuration provided via the `process.env` JSON object in the `build/webpack.ENV.js` files will be available via `process.env` in all Vue.js files. The values of `build/webpack.dev.js` will be used when running `yarn dev`, the values of `build/webpack.prod.js` for `yarn build`.

Please note that all provided configuration is visible to clients, since they will be included in the JavaScript loaded by the browser. You should not not include any secrets or otherwise confidential data.  
Configuration values are only modifyable during transpilation - changing them requires you to rebuild the project.

#### Transpile and minify Vue.js/JS sources
```sh
$ yarn build
```

## Usage
Once transpiled and minifed, you will only have to serve the content of the `dist/` folder created. Any webserver that can serve HTML, JS and CSS as well as some small images should suffice, however I suggest using either [nginx](https://www.nginx.com/) or [Apache2](https://httpd.apache.org/).

Optionally, you can use Docker and the provided Dockerfile to run the frontend using a minimal nginx installation in a Docker container. Please make sure to check and adapt the included nginx configuration in the `nginx/` folder as required.

#### Start using Docker
```sh
$ docker build -t slotlist-frontend .
$ docker run -p 4000:4000 slotlist-frontend
```

## Development
The easiest way to start developing is by setting up the required Node/Yarn environment and running `yarn dev`. Your sources will be transpiled using webpack and the original source folder will be watched for changes, automatically rebuilding and reloading as required.

In order to allows for easier development and debugging, the Vue devtools extension for [Google Chrome](https://chrome.google.com/webstore/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd) or [Mozilla Firefox](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/) is highly recommended since it provides additional insight, especially into the vuex store and allows for on-the-fly modifications.

## Deployment
slotlist-frontend was designed to be deployed to a Kubernetes cluster running on the [Google Cloud Platform](https://cloud.google.com/). The `k8s/` folder contains the configuration files required to create and run all services. This project also depends on the rest of the infrastructure being set up via the Kubernetes configs provided in the [slotlist-backend](hhttps://github.com/Black-Forest-Community/slotlist-reboot) project. A `cloudbuild.yaml` file for automatic Docker image builds is provided in the repository root as well.

Generally speaking, slotlist-frontend can be deployed anywhere running a webserver capable of serving static content.

[Let's Encrypt](https://letsencrypt.org/) provides excellent, free SSL certificates that are easy to integrate into your existing hosting, so there's no reason why you should run your site over plain HTTP!

Please be advised that some configuration values might need modifications should you plan to run your own instance since they have been tailored to work for [slotlist.online](https://slotlist.online)'s main instance. This is especially relevant for the CSP/HPKP headers set - failing to set these properly will result in problems loading your site.

## License
[MIT](https://choosealicense.com/licenses/mit/)

