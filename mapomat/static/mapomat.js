angular.module('mapomat', [])
    .controller('SelectController', function SelectController($window) {
        this.cityCats = $window.cityCategories
        this.superNames = $window.superCatNames
        this.subNames = $window.subCatNames
      });
