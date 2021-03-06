

// This will need to be changed to refer to your own utils script
var utils = require('users/ipdavies/CPR:Exports/utils_HRNHD');

var bands = ['elevation', 'slope', 'curve', 'aspect', 'hand', 'spi', 'twi', 'sti',
             'landcover', 'GSWPerm', 'GSWDistSeasonal', 'flooded']

// For spectral bands
// var bands = ['B1','B2','B3','B4','B5','B6','B7']

// Export bands individually to Google Drive
function export_bands_drive(imageID, dfoID, batch, geometry){
  var features = utils.featuresFromID(imageID)
  features = features.unmask(-999999)

  for (var i=0; i<bands.length; i++){
    Export.image.toDrive({
      image: features.select(bands[i]).toFloat().clip(geometry),
      description: dfoID + '_' +imageID+'_'+batch+'_'+bands[i],
      folder: 'GEE_exports8',
      scale: 30,
      region: geometry
    })
  }
}


// // All bands in one .tif instead of separate
// function export_bands_drive(imageID, dfoID, batch, geometry){
//   var features = utils.featuresFromID(imageID)
//   features = features.unmask(-999999)
//   Export.image.toDrive({
//     image: features.toFloat().clip(geometry),
//     description: dfoID + '_' +imageID+'_'+batch,
//     folder: 'GEE_exports',
//     scale: 30,
//     region: geometry
//   })
// }


 //======================================================================
 var imageID = 'LC08_021033_20131227'
 var dfoID = 4115
 var batch = 1

 var geometry = ee.Geometry.Polygon(
         [[[-86.5452202752047, 39.05806789856563],
           [-86.5452202752047, 38.56798285071334],
           [-85.86681451348595, 38.56798285071334],
           [-85.86681451348595, 39.05806789856563]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 var imageID = 'LC08_021033_20131227'
 var dfoID = 4115
 var batch = 2

 var geometry = ee.Geometry.Polygon(
         [[[-87.39940728692345, 38.979112347602914],
           [-87.39940728692345, 38.4884826399847],
           [-86.7210015252047, 38.4884826399847],
           [-86.7210015252047, 38.979112347602914]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 // Not much flooding, consider removing
 var imageID = 'LC08_027038_20131103'
 var dfoID = 4101
 var batch = 1

 var geometry =  ee.Geometry.Polygon(
         [[[-97.37636651543906, 31.533428089720257],
           [-97.37636651543906, 30.995803169402503],
           [-96.69796075372031, 30.995803169402503],
           [-96.69796075372031, 31.533428089720257]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 var imageID = 'LC08_027039_20131103'
 var dfoID = 4101
 var batch = 1

 var geometry = ee.Geometry.Polygon(
         [[[-98.04584588555625, 30.34675136983907],
           [-98.04584588555625, 29.802463106006105],
           [-97.3674401238375, 29.802463106006105],
           [-97.3674401238375, 30.34675136983907]]], null, false)
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 var imageID = 'LC08_026038_20160325'
 var dfoID = 4337
 var batch = 1

 var geometry = ee.Geometry.Polygon(
         [[[-96.71512689141562, 32.66129105657018],
           [-96.71512689141562, 32.13021486559879],
           [-96.03672112969687, 32.13021486559879],
           [-96.03672112969687, 32.66129105657018]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 var imageID = 'LC08_026038_20160325'
 var dfoID = 4337
 var batch = 2

 var geometry = ee.Geometry.Polygon(
         [[[-96.16031732110312, 32.15114574227692],
           [-96.16031732110312, 31.617081619136826],
           [-95.48191155938437, 31.617081619136826],
           [-95.48191155938437, 32.15114574227692]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 var imageID = 'LC08_026038_20160325'
 var dfoID = 4337
 var batch = 3

 var geometry = ee.Geometry.Polygon(
         [[[-95.88840570000937, 31.373517697119393],
           [-95.88840570000937, 30.834981236339175],
           [-95.20999993829062, 30.834981236339175],
           [-95.20999993829062, 31.373517697119393]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 var imageID = 'LC08_021033_20131227'
 var dfoID = 4115
 var batch = 'test'

 var geometry = ee.Geometry.Polygon(
         [[[-87.13895292,	38.4391461],
           [-86.94531889,	38.4391461],
           [-86.94531889,	38.58958082],
           [-87.13895292,	38.58958082],
           [-87.13895292,	38.4391461]]]);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 // Tons of clouds in image
 var imageID = 'LC08_022034_20180404'
 var dfoID = 4594
 var batch = 1
 var geometry = ee.Geometry.Polygon(
         [[[-89.28562249688437, 37.28383706109734],
           [-89.28562249688437, 36.78174159149698],
           [-88.60721673516562, 36.78174159149698],
           [-88.60721673516562, 37.28383706109734]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 // River flooding, small
 var imageID = 'LC08_027033_20170826'
 var dfoID = 4514
 var batch = 1
 var geometry = ee.Geometry.Polygon(
         [[[-95.20999993829062, 38.615748109446955],
           [-95.20999993829062, 38.12262395392177],
           [-94.53159417657187, 38.12262395392177],
           [-94.53159417657187, 38.615748109446955]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 // Farmland flooding, signficant cloud cover
 var imageID = 'LC08_022033_20170519'
 var dfoID = 4477
 var batch = 1
 var geometry = ee.Geometry.Polygon(
         [[[-88.46988763360312, 38.54274568007013],
           [-88.46988763360312, 38.04912278643827],
           [-87.79148187188437, 38.04912278643827],
           [-87.79148187188437, 38.54274568007013]]], null, false)
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 // River flooding, large
 var imageID = 'LC08_022035_20170503'
 var dfoID = 4468
 var batch = 1
 var geometry = ee.Geometry.Polygon(
         [[[-89.58774652032187, 36.24089948694252],
           [-89.58774652032187, 35.73197018785879],
           [-88.90934075860312, 35.73197018785879],
           [-88.90934075860312, 36.24089948694252]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 var imageID = 'LC08_024036_20170501'
 var dfoID = 4468
 var batch = 1
 var geometry = ee.Geometry.Polygon(
         [[[-91.95530023125937, 34.22878317129099],
           [-91.95530023125937, 33.70715254681783],
           [-91.27689446954062, 33.70715254681783],
           [-91.27689446954062, 34.22878317129099]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 var imageID = 'LC08_024036_20170501'
 var dfoID = 4468
 var batch = 2
 var geometry = ee.Geometry.Polygon(
         [[[-92.17502679375937, 34.78104780981504],
           [-92.17502679375937, 34.262839313651554],
           [-91.49662103204062, 34.262839313651554],
           [-91.49662103204062, 34.78104780981504]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 var imageID = 'LC08_024036_20170501'
 var dfoID = 4468
 var batch = 3

 var geometry = ee.Geometry.Polygon(
         [[[-92.88089837579062, 35.29153793847362],
           [-92.88089837579062, 34.77653594236694],
           [-92.20249261407187, 34.77653594236694],
           [-92.20249261407187, 35.29153793847362]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 // River flooding, small
 var imageID = 'LC08_015035_20170502'
 var dfoID = 4469
 var batch = 1
 var geometry = ee.Geometry.Polygon(
         [[[-78.07682122735312, 35.72193653876053],
           [-78.07682122735312, 35.20967004704892],
           [-77.39841546563437, 35.20967004704892],
           [-77.39841546563437, 35.72193653876053]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 var imageID = 'LC08_043034_20170303'
 var dfoID = 4444
 var batch = 1
 var geometry = ee.Geometry.Polygon(
         [[[-121.05602349786095, 37.42520231906159],
           [-121.05602349786095, 36.92404612375649],
           [-120.3776177361422, 36.92404612375649],
           [-120.3776177361422, 37.42520231906159]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 var imageID = 'LC08_044034_20170222'
 var dfoID = 4444
 var batch = 1
 var geometry = ee.Geometry.Polygon(
         [[[-121.58817376641562, 37.963638964184355],
           [-121.58817376641562, 37.466088477766576],
           [-120.90976800469687, 37.466088477766576],
           [-120.90976800469687, 37.963638964184355]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 var imageID = 'LC08_045032_20170301'
 var dfoID = 4444
 var batch = 1
 var geometry = ee.Geometry.Polygon(
         [[[-122.520638366025, 39.76627671413745],
           [-122.520638366025, 39.28111903119737],
           [-121.84223260430625, 39.28111903119737],
           [-121.84223260430625, 39.76627671413745]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 var imageID = 'LC08_045032_20170301'
 var dfoID = 4444
 var batch = 2

 var geometry = ee.Geometry.Polygon(
         [[[-122.53437127618125, 40.271095501472246],
           [-122.53437127618125, 39.78949586707858],
           [-121.8559655144625, 39.78949586707858],
           [-121.8559655144625, 40.271095501472246]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 // Significant cloud cover, much of it transparent but cloud mask might cover it up anyways
 var imageID = 'LC08_044033_20170222'
 var dfoID = 4444
 var batch = 1
 var geometry = ee.Geometry.Polygon(
         [[[-121.99054803399375, 39.30237569253474],
           [-121.99054803399375, 38.81398190702264],
           [-121.312142272275, 38.81398190702264],
           [-121.312142272275, 39.30237569253474]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 // Significant cloud cover, much of it transparent but cloud mask might cover it up anyways
 var imageID = 'LC08_044033_20170222'
 var dfoID = 4444
 var batch = 2
 var geometry = ee.Geometry.Polygon(
         [[[-121.78249444512656, 38.45353925382679],
           [-121.78249444512656, 37.959308018754676],
           [-121.10408868340781, 37.959308018754676],
           [-121.10408868340781, 38.45353925382679]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 var imageID = 'LC08_034032_20130917'
 var dfoID = 4089
 var batch = 1
 var geometry = ee.Geometry.Polygon(
         [[[-105.25768365411093, 40.55863003109763],
           [-105.25768365411093, 40.07907389634886],
           [-104.57927789239218, 40.07907389634886],
           [-104.57927789239218, 40.55863003109763]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 var imageID = 'LC08_028034_20130806'
 var dfoID = 4080
 var batch = 1
 var geometry = ee.Geometry.Polygon(
         [[[-98.21956719903281, 38.40189959188772],
           [-98.21956719903281, 37.90731675418927],
           [-97.54116143731406, 37.90731675418927],
           [-97.54116143731406, 38.40189959188772]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 // Cloud cover
 var imageID = 'LC08_025031_20130529'
 var dfoID = 4061
 var batch = 1
 var geometry = ee.Geometry.Polygon(
         [[[-91.24050225762656, 41.32727889640181],
           [-91.24050225762656, 40.85324531831005],
           [-90.56209649590781, 40.85324531831005],
           [-90.56209649590781, 41.32727889640181]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 // Significant cloud cover
 var imageID = 'LC08_025031_20130529'
 var dfoID = 4061
 var batch = 2
 var geometry = ee.Geometry.Polygon(
         [[[-92.29244317559531, 41.56198464926667],
           [-92.29244317559531, 41.08965460892531],
           [-91.61403741387656, 41.08965460892531],
           [-91.61403741387656, 41.56198464926667]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 // Significant cloud cover
 var imageID = 'LC08_025031_20130529'
 var dfoID = 4061
 var batch = 3
 var geometry = ee.Geometry.Polygon(
         [[[-92.41603936700156, 42.22643679767548],
           [-92.41603936700156, 41.758972829744614],
           [-91.73763360528281, 41.758972829744614],
           [-91.73763360528281, 42.22643679767548]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)


 //======================================================================
 // Mostly regular river flooding, some farmland
 var imageID = 'LC08_023036_20130429'
 var dfoID = 4050
 var batch = 1
 var geometry = ee.Geometry.Polygon(
         [[[-90.71041192559531, 35.433768464779035],
           [-90.71041192559531, 34.91966721181415],
           [-90.03200616387656, 34.91966721181415],
           [-90.03200616387656, 35.433768464779035]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 var imageID = 'LC08_023036_20130429'
 var dfoID = 4050
 var batch = 2
 var geometry = ee.Geometry.Polygon(
         [[[-91.01253594903281, 34.85658489747442],
           [-91.01253594903281, 34.338848254804645],
           [-90.33413018731406, 34.338848254804645],
           [-90.33413018731406, 34.85658489747442]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

 //======================================================================
 var imageID = 'LC08_023036_20130429'
 var dfoID = 4050
 var batch = 3
 var geometry = ee.Geometry.Polygon(
         [[[-91.17733087090781, 34.42045278532338],
           [-91.17733087090781, 33.90000432273006],
           [-90.49892510918906, 33.90000432273006],
           [-90.49892510918906, 34.42045278532338]]], null, false);
 export_bands_drive(imageID, dfoID, batch, geometry)

//======================================================================
var imageID = 'LC08_028034_20130806'
var dfoID = 4080
var batch = 'test'
var geometry = ee.Geometry.Polygon(
        [[[-98.2272213095015, 38.361115320614964],
          [-98.2272213095015, 37.918275360992354],
          [-97.61473351653275, 37.918275360992354],
          [-97.61473351653275, 38.361115320614964]]], null, false);
export_bands_drive(imageID, dfoID, batch, geometry)



