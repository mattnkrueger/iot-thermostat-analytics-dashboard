#include <fstream>
#include <iostream>
#include <string>
#include <httplib.h>
#include <json.hpp>
#include <unistd.h>
#include "rpi1306i2c.hpp"
#include <sstream>
#include <iomanip>
#include <wiringPi.h>
#include <time.h>
#include <stdio.h>

using json = nlohmann::json;

const int BUTTON_SENSOR1 = 27;
const int BUTTON_SENSOR2 = 22;
const int POWER_SWITCH = 23;

volatile bool sensor1Enabled = false;
volatile bool sensor2Enabled = false;
volatile bool sensor1Unplugged = false;
volatile bool sensor2Unplugged = false;

bool systemActive = false;
bool lastSystemActive = false;

const    unsigned int DEBOUNCE_DELAY = 100;
volatile unsigned int lastPressTime1 = 0;
volatile unsigned int lastPressTime2 = 0;

void buttonCallback(int buttonPin, volatile unsigned int& lastPressTime, volatile bool& sensorEnabled) {
    if (!systemActive) return; 

    unsigned int currentTime = millis();
    if (currentTime - lastPressTime > DEBOUNCE_DELAY) {
        sensorEnabled = !sensorEnabled;
        std::cout << "Sensor " << (buttonPin == BUTTON_SENSOR1 ? "1" : "2") << " toggled to " << (sensorEnabled ? "ON" : "OFF") << std::endl;
        lastPressTime = currentTime;
    }
}

void button1Interrupt() {
    buttonCallback(BUTTON_SENSOR1, lastPressTime1, sensor1Enabled);
}

void button2Interrupt() {
    buttonCallback(BUTTON_SENSOR2, lastPressTime2, sensor2Enabled);
}

double readTemperature(const std::string &devicePath) {
    std::ifstream file(devicePath + "/w1_slave");
    std::string line1, line2;

    if (!std::getline(file, line1) || !std::getline(file, line2)) {
        throw std::runtime_error("Failed to read sensor file");
    }

    if (line1.find("YES") == std::string::npos) {
        throw std::runtime_error("CRC check failed");
    }

    size_t tEqualsPosition = line2.find("t=");
    if (tEqualsPosition == std::string::npos) {
        throw std::runtime_error("Temperature not found");
    }

    int milliCelsius = std::stoi(line2.substr(tEqualsPosition + 2));
    return milliCelsius / 1000.0;  
}

// ===================================================================== //
//                              MAIN CODE                                //
// ===================================================================== //
int main() {
    // ================ //
    //  INITIALIZATION  //
    // ================ //
	// 0: Setup ENV
	std::cout << "[INIT] Setting up environment" << std::endl;
	const char* host_env = std::getenv("HOST");
	const char* port_env = std::getenv("PORT");

	std::string host = host_env ? host_env : "localhost";
	int port = port_env ? std::stoi(port_env) : 8050;

	// 1: Setup HTTP Connection With Stream Writer Server
	std::cout << "[INIT] Starting Sensor Program" << std::endl;
	const std::string url = "http://" + host + ":" + std::to_string(port);
	
	std::cout << "[INIT] Connecting to " << url << std::endl;
	httplib::Client client(host, port);
	client.set_connection_timeout(5);
	client.set_read_timeout(5, 0);

	std::cout << "[INIT] Performing Healthcheck" << std::endl;
	auto res = client.Get("/");
	if (res && res->status == 200) {
		std::cout << "[INIT] HEALTHY!" << std::endl;
	} else if (res) {
		std::cerr << "[INIT] Health Check failed." << std::endl;
	} else {
		std::cerr << "[INIT] ERROR: Could not reach server" << std::endl;
	}
	
	// 2. Screen Initialization
	std::cout << "[INIT] Setting up Display" << std::endl;
	ssd1306::Display128x32 screen(1, 0x3C);
	screen.clear();

	// 3. WiringPi Initialization
	std::cout << "[INIT] Setting up WiringPi" << std::endl;
	if (wiringPiSetupGpio() == -1) {
		std::cerr << "WiringPi initialization failed." << std::endl;
		return 1;
	}

	pinMode(BUTTON_SENSOR1, INPUT);
	pullUpDnControl(BUTTON_SENSOR1, PUD_UP);
	if (wiringPiISR(BUTTON_SENSOR1, INT_EDGE_FALLING, &button1Interrupt) < 0) {
		std::cerr << "[INIT] ERROR: Unable to set up ISR for BUTTON 1." << std::endl;
		return 1;
	}

	pinMode(BUTTON_SENSOR2, INPUT);
	pullUpDnControl(BUTTON_SENSOR2, PUD_UP);
	if (wiringPiISR(BUTTON_SENSOR2, INT_EDGE_FALLING, &button2Interrupt) < 0) {
		std::cerr << "[INIT] ERROR: Unable to set up ISR for BUTTON 2." << std::endl;
		return 1;
	}
	
	// 4. State Initialization
	unsigned int lastReadTime = 0;
	const unsigned int READ_INTERVAL = 1000;
	bool lastSensor1Enabled = false;
	bool lastSensor2Enabled = false;
	std::string unit = "C";  

	screen.drawString(0, 0, "Sensor 1: OFF");
	screen.drawString(0, 0, "Sensor 2: OFF");

	pinMode(POWER_SWITCH, INPUT);
	pullUpDnControl(POWER_SWITCH, PUD_DOWN);

	systemActive = (digitalRead(POWER_SWITCH) == HIGH);
	lastSystemActive = systemActive;

	if (!systemActive) {
		screen.clear();
	}

	std::cout << std::endl;
    // ================ //
    //   PROGRAM LOOP   //
    // ================ //
	while (true) {
		unsigned int currentTime = millis();

		systemActive = (digitalRead(POWER_SWITCH) == HIGH);

        // timing
        if (currentTime - lastReadTime >= READ_INTERVAL) {

            // ====================================================================================== //
            //                                  SYSTEM INACTIVE                                       //
            // ====================================================================================== //

            if (!systemActive) {
                if (lastSystemActive) {                                                                           
                    //////////////////////////
                    //   CLEAR LCD SCREEN   //
                    //////////////////////////
                    lastSystemActive = false;
                    screen.clear();
                    std::cout << "(" << currentTime << ")" << "System Off" << std::endl;

                    //////////////////////////////
                    //   HIT /turnOFF ENDPOINT  //
                    //////////////////////////////
                    auto res = client.Get("/turnOFF");

                    if (res && res->status == 200) {
                        std::cout << "[TURN OFF] SUCCESS!" << std::endl;
                    } else if (res) {
                        std::cerr << "[TURN OFF] error" << std::endl;
                    } else {
                        std::cerr << "[TURN OFF] ERROR: Could not reach server" << std::endl;
                    }
                }

                continue;
            }

            // ====================================================================================== //
            //                                  SYSTEM ACTIVE                                         //
            // ====================================================================================== //
            lastSystemActive = true;

            //////////////////
            //   SENSOR 1   //
            //////////////////

            // get temperatures  
            double temperature1 = 0.0;
            try {                                                            
                temperature1 = readTemperature("/sys/bus/w1/devices/28-000010eb7a80");
                if (temperature1 > 63) temperature1 = 63;
                if (temperature1 < -10) temperature1 = -10;
                sensor1Unplugged = false;
            } catch (const std::exception &e) {                            
                sensor1Unplugged = true;
            }

            // display to screen
            std::ostringstream ss1;
            if (sensor1Enabled && !sensor1Unplugged) {                                                                                  
                double tempTemp1 = (unit == "F") ? (temperature1 * 9 / 5.0 + 32) : temperature1;
                ss1 << "Sensor 1: " << std::fixed << std::setprecision(2) << tempTemp1 << " " << unit << "    ";
            } 
            else if (!sensor1Enabled && !sensor1Unplugged) {                                                                            
                ss1 << "Sensor 1: OFF        ";
            }
            else if (sensor1Unplugged) {                                                                          
                ss1 << "Sensor 1: Unplugged ";
            }

            //////////////////
            //   SENSOR 2   //
            //////////////////

            // get temperatures  
            double temperature2 = 0.0;
            try {                                                            
                temperature2 = readTemperature("/sys/bus/w1/devices/28-000007292a49");
                if (temperature2 > 63) temperature2 = 63;
                if (temperature2 < -10) temperature2 = -10;
                sensor2Unplugged = false;
            } catch (const std::exception &e) {                            
                sensor2Unplugged = true;
            }

            // display to screen
            std::ostringstream ss2;
            if (sensor2Enabled && !sensor2Unplugged) {                                                                                  
                double tempTemp2 = (unit == "F") ? (temperature2 * 9 / 5.0 + 32) : temperature2;
                ss2 << "Sensor 2: " << std::fixed << std::setprecision(2) << tempTemp2 << " " << unit << "    ";
            } 
            else if (!sensor2Enabled && !sensor2Unplugged) {                                                                            
                ss2 << "Sensor 2: OFF        ";
            }
            else {                                                                          
                ss2 << "Sensor 2: Unplugged ";
            }

            // draw both
            screen.drawString(0, 0, ss1.str());
            screen.drawString(0, 8, ss2.str());

            ///////////////////////////////////
            // POST DATA TO /temperatureData //
            ///////////////////////////////////
            struct timeval tv;
            time_t now     = time(NULL);
            long timestamp = (long)now;

            json json_data;

            json_data["timestamp"] = timestamp;
            
            if (sensor1Unplugged) {
                json_data["sensor1Unplugged"] = sensor1Unplugged;
            } else {
                json_data["sensor1Enabled"] = sensor1Enabled;
                json_data["sensor1Temperature"] = sensor1Enabled ? json(temperature1) : json(nullptr);
            }

            if (sensor2Unplugged) {
                json_data["sensor2Unplugged"] = sensor2Unplugged;
            } else {
                json_data["sensor2Enabled"] = sensor2Enabled;
                json_data["sensor2Temperature"] = sensor2Enabled ? json(temperature2) : json(nullptr);
            }

            auto res = client.Post("/temperatureData", json_data.dump(), "application/json");
            
            ///////////////////////////////////
            // HANDLE SERVER VIRTUALIZATION  //
            ///////////////////////////////////
            if (res) {
                json j = json::parse(res->body);

                unit = j[0].get<std::string>();
                if (j[1].get<bool>()) {
                    buttonCallback(BUTTON_SENSOR1, lastPressTime1, sensor1Enabled);
                }
                if (j[2].get<bool>()) {
                    buttonCallback(BUTTON_SENSOR2, lastPressTime2, sensor2Enabled);
                }
            } else {
                std::cout << "Error: " << res.error() << std::endl;
            }
        }
    }
}
