<?php

/**
  * @author Chandu <gummalla.chandu@gmail.com>
  */

class Weather 
{
    Private $Rainy = 1.2; // to be hiked by 20%  
    Private $Sunny = 0.9; // to be decreased by 10%  
    Private $Windy = 1; // no action for now  
   
    //  find the craters as per weather
    function getCraterCount($climate,$orbit_craters)
    {
        if($climate == 'RAINY')  
            $craters = $orbit_craters*$this->Rainy;
        elseif($climate == 'SUNNY')  
            $craters = $orbit_craters*$this->Sunny;
        elseif($climate == 'WINDY'){  
            $craters = $orbit_craters*$this->Windy;
        }
        return $craters;
    }

}

class Vehicle extends Weather
{
    private $bike_speed = 10;
    private $tuktuk_speed = 12;
    private $car_speed = 20;

    private $bike_min_craters = 2;
    private $tuktuk_min_craters = 1;
    private $car_min_craters = 3;
    

    function getVehicleStandardSpeed($vehicle, $climate, $orbit_craters)
    {
        if($vehicle == "BIKE"){
            $cratersCount = parent::getCraterCount($climate,$orbit_craters);
            return $standardSpeed = $cratersCount*$this->bike_min_craters;
        }
        elseif($vehicle == "TUKTUK"){
            $cratersCount = parent::getCraterCount($climate,$orbit_craters);
            return $standardSpeed = $cratersCount*$this->tuktuk_min_craters;
        }
        elseif($vehicle == "CAR"){
            $cratersCount = parent::getCraterCount($climate,$orbit_craters);
            return $standardSpeed = $cratersCount*$this->car_min_craters;
        }
    }
    
    function getVehicleOptimisedSpeed($orbit_standard_distance, $input_speed, $vehicle)
    {
        if($vehicle == "BIKE"){ 
            return ($orbit_standard_distance/min($this->bike_speed,$input_speed))*60;
        }if($vehicle == "TUKTUK"){ 
            return ($orbit_standard_distance/min($this->tuktuk_speed,$input_speed))*60;
        }if($vehicle == "CAR"){ 
            return ($orbit_standard_distance/min($this->car_speed,$input_speed))*60;
        }    
    }
    
    function getActualSpeed($orbit_standard_distance, $input_speed, $vehicle, $climate, $orbit_craters)
    {
        return $this->getVehicleStandardSpeed($vehicle, $climate, $orbit_craters) + $this->getVehicleOptimisedSpeed($orbit_standard_distance, $input_speed, $vehicle);
        
    }
    
}

class orbit extends Vehicle
{
    private $orbit_1_distance = 18;
    private $orbit_2_distance = 20;
    private $orbit_1_craters = 20;
    private $orbit_2_craters = 10;

    private $rainy_vehicles = ["TUKTUK", "CAR"];
    private $windy_vehicles = ["BIKE", "CAR"];
    private $sunny_vehicles = ["BIKE", "TUKTUK", "CAR"];
    
    function bestRoute($weather,$orbit_1_speed,$orbit_2_speed)
    {
        $orbit_1 = $orbit_2 = array(); 
        
        if($weather == 'RAINY'){
            foreach($this->rainy_vehicles as $vehicle){
                $orbit_1[parent::getActualSpeed($this->orbit_1_distance, $orbit_1_speed, $vehicle, $weather, $this->orbit_1_craters)] = $vehicle;
                $orbit_2[parent::getActualSpeed($this->orbit_2_distance, $orbit_2_speed, $vehicle, $weather, $this->orbit_2_craters)] = $vehicle;
            }
        }
        if($weather == 'WINDY'){
            foreach($this->windy_vehicles as $vehicle){
                $orbit_1[parent::getActualSpeed($this->orbit_1_distance, $orbit_1_speed, $vehicle, $weather, $this->orbit_1_craters)] = $vehicle;
                $orbit_2[parent::getActualSpeed($this->orbit_2_distance, $orbit_2_speed, $vehicle, $weather, $this->orbit_2_craters)] = $vehicle;
            }
        }
        if($weather == 'SUNNY'){
            foreach($this->sunny_vehicles as $vehicle){
                $orbit_1[parent::getActualSpeed($this->orbit_1_distance, $orbit_1_speed, $vehicle, $weather, $this->orbit_1_craters)] = $vehicle;
                $orbit_2[parent::getActualSpeed($this->orbit_2_distance, $orbit_2_speed, $vehicle, $weather, $this->orbit_2_craters)] = $vehicle;
            }
        }  
        $result = $orbit_1 + $orbit_2; $fastest = min(array_keys($result)); 
        if(array_key_exists($fastest, $orbit_1)){
            $output = $result[$fastest].' '."ORBIT1";
        }
        if(array_key_exists($fastest, $orbit_2)){
            $output = $result[$fastest].' '."ORBIT2";
        }
        echo $output;   
    }

    function fileProcessing(){
        $file = fopen("input.txt","r");
        while(! feof($file))
        {
            $inputs=explode(" ",fgets($file));
            if(strlen($inputs[0])>0 && strlen($inputs[1])>0 && strlen($inputs[2])>0)
            $this->bestRoute($inputs[0],(int)$inputs[1],(int)$inputs[2]);
        }
        fclose($file);
    }
    

}
$processObject = new orbit();
$processObject->fileProcessing();

?>