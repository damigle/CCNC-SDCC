/* 
 *  Programa: Controlador do hardware do CCNC_SDCC
 *  vsersao: 1.3 
 *  data: 14 de novembro 2020
 *  Desenvolvedores:  Karan
 *                    Rubens Damigle
 *                    Francisco Geraldo
 *                    
 *  Observacoes:
 *              Desenvolvido como trabalho de conclusao
 *              de curso
 */

#include <OneWire.h>  
#include <DallasTemperature.h>
#include <Adafruit_MCP4725.h>

#define ONE_WIRE_BUS1 7
#define ONE_WIRE_BUS2 5

//****************************************************

// variaveis tipo GLOBAL
int bomba = 13;
int valvula = 12 ;
char cmd;
const long period = 1000;
float settemp,t_inf,t_sup,t_dif,erro,ierro,Kp,Kd,Ki,PDI,S,P1,P2,T,Pot;
float cnterro;
float xerro;
String tss;

//***************************************************************

OneWire oneWire1(ONE_WIRE_BUS1);
OneWire oneWire2(ONE_WIRE_BUS2);

//DeviceAddress sensor1;
//DeviceAddress sensor2;

Adafruit_MCP4725 dac;

DallasTemperature sensor1(&oneWire1);
DallasTemperature sensor2(&oneWire2);


//****************************************************

void setup(){

  Serial.begin(38400); //inic. porta de comunicacao
  //Serial.setTimeout(3000);
  dac.begin(0x60);    //inic. conversor D/A
  sensor1.begin();   //inic. sensor1 de temperatura
  sensor2.begin();   //inic. sensor2 de temperatura

  pinMode(bomba, OUTPUT);
  pinMode(valvula, OUTPUT);  
  
  cnterro=0;
  xerro=0;
  settemp=0.0; //por exemplo 0.0 graus de diferença.
  erro=0.0;
  ierro=0.0;
  desligaBomba();
  fechaValvula();
}
//****************************************************
//**********************************************************

void SOther()
{
      settemp = Serial.parseFloat();
      Serial.println("Set diferença Temp=");
      Serial.println(settemp);
}

void Supersaturacao1()
{
  ierro=0;
  cnterro=0;
  settemp = 4.86;
}

void Supersaturacao01()
{
  ierro=0;
  cnterro=0;
  settemp = 1.57;
}

void Supersaturacao02()
{
  ierro=0;
  cnterro=0;
  settemp = 2.22;
}

void Supersaturacao03()
{
  ierro=0;
  cnterro=0;
  settemp = 2.74;
}

void Supersaturacao04()
{
  ierro=0;
  cnterro=0;
  settemp = 3.14;
}

void Supersaturacao05()
{
  ierro=0;
  cnterro=0;
  settemp = 3.48;
}

void Supersaturacao06()
{
  ierro=0;
  cnterro=0;
  settemp = 3.82;
}

void Supersaturacao07()
{
  ierro=0;
  cnterro=0;
  settemp = 4.12;
}

void Supersaturacao08()
{
  ierro=0;
  cnterro=0;
  settemp = 4.40;
}

void Supersaturacao09()
{
  ierro=0;
  cnterro=0;
  settemp = 4.66;
}

void resetTemp()
{
  ierro=0;
  cnterro=0;
  settemp = 0; //era t_dif
}

//****************************************************

void ligaBomba()
{
  digitalWrite(bomba,LOW);
}

//****************************************************

void desligaBomba()
{
  digitalWrite(bomba,HIGH);
}

//****************************************************

void abreValvula()
{
  digitalWrite(valvula,LOW);
}

//****************************************************

void fechaValvula()
{
  digitalWrite(valvula,HIGH);
}

//*****************************************************************************

void leTemperatura()
{
  sensor1.requestTemperatures(); // Send the command to get temperatures
  sensor2.requestTemperatures(); // Send the command to get temperatures  
  t_inf=sensor1.getTempCByIndex(0);
  t_sup=sensor2.getTempCByIndex(0);
  t_dif=t_sup-t_inf;
}

//*****************************************************************************************************************************

void leSaturacao()
{
  T = ((t_sup)/2)+(t_inf/2);
  P1 = ((0.61078*(pow(2.718282,((17.269*t_sup)/(t_sup + 237.3)))) + 0.61078*(pow(2.718282,((17.269*t_inf)/(t_inf + 237.3)))))/2);
  P2 = 0.61078*(pow(2.718282,((17.269*T)/(T + 237.3))));
  S = ((P1/P2)*100) - 100;
}

//*******************************************************************************************************************************

void envia_dados() 
{ 

  leTemperatura();
  Serial.print(t_sup);
  Serial.print("  ");  
  Serial.print(t_inf);
  Serial.print("  "); 
  if(cnterro>5) xerro=99.00;
  Serial.println(xerro);
}

//****************************************************

void leComando()
{ 
  char cmd;
  cmd = Serial.read();
   if (cmd == 'S') envia_dados();
   if (cmd == 'L') ligaBomba();
   if (cmd == 'D') desligaBomba();
   if (cmd == 'A') abreValvula();
   if (cmd == 'F') fechaValvula();
   if (cmd == 'J') Supersaturacao1();
   if (cmd == 'E') Supersaturacao01();
   if (cmd == 'H') Supersaturacao02();
   if (cmd == 'Z') Supersaturacao03();
   if (cmd == 'V') Supersaturacao04();
   if (cmd == 'M') Supersaturacao05();
   if (cmd == 'N') Supersaturacao06();
   if (cmd == 'Y') Supersaturacao07();
   if (cmd == 'I') Supersaturacao08();
   if (cmd == 'O') Supersaturacao09();
   if (cmd == 'P') resetTemp();
   if (cmd == 'T') SOther();
}


//***********************************************************

void ctrlTemp()
{
  uint32_t saida;
  erro=(t_sup-t_inf)-settemp;
  erro=-erro;
  if(abs(erro)<0.3) cnterro=cnterro+1;
  if(abs(erro)>0.3) xerro=0.0;
  
  
  ierro=ierro+erro;
  //derro=erro-eold;
  Kp=0.5*erro; //1.0*erro;
  Kd=0.0;
  Ki=0.1*ierro; //ERA 0.003
  PDI=(Kp+Ki+Kd);
  Pot=-409.5*PDI+2047.67;
  if(Pot<0) Pot=0;
  saida=round(Pot);
  dac.setVoltage(saida, false); 
}

//****************************************************

void loop()
{
  if (Serial.available() > 0) leComando();
  leTemperatura();
  leSaturacao();
  ctrlTemp();
 
 }
