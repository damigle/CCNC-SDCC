import os, sys
import threading

import gi
#import keyboard as keyboard

from  pynput import keyboard
import serial
import time
import cv2
import json
import numpy as np
from threading import Thread
from time import sleep
from PIL import Image, ImageFilter
from datetime import datetime, date
from matplotlib import pyplot as plt
from openpyxl import load_workbook

import main

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib


########################################################################################################################

IWD = 640
IHD = 480
IH1 = 206
IH2 = 262
IW1 = 10
IW2 = 630
IHDM = int(IHD / 2)
IWDM = int(IWD / 2)
IH1_thr = 140
IH2_thr = 180
#BW = [[0 for y in range(IHD)] for x in range(IWD)]
bw_antigo = [[0 for y in range(IHD)] for x in range(IWD)]
bw_atual = [[0 for y in range(IHD)] for x in range(IWD)]
bw_soma = [[0 for y in range(IHD)] for x in range(IWD)]

curva=[0 for y in range(100)]
tempo=[0 for y in range(100)]

xmg1 = None
xss = None
lss = [False, False, False, False, False, False, False, False, False, False]
cmd_ss = ['E', 'H', 'Z', 'V', 'M', 'N', 'Y', 'I', 'O', 'J']
cap = None
cmd = {"ccnc": "X",
       "ss01_ck": True,
       "ss02_ck": False,
       "ss03_ck": False,
       "ss04_ck": False,
       "ss05_ck": False,
       "ss06_ck": False,
       "ss07_ck": False,
       "ss08_ck": False,
       "ss09_ck": False,
       "ss10_ck": False,
       "bomba": 0,
       "valvula": 0,
       "reiniciar_temp": ""}

with open("ccnc.cfg", "r") as f:
    cfg = json.load(f)

########################################################################################################################
#Keyboard monitoring functions
########################################################################################################################

STOP_PROGRAM = 0
def on_press(key):
        pass

def on_release(key):
    if key == keyboard.Key.esc:
        print('{0} released'.format(key))
        main.STOP_PROGRAM = 1
        return False

def on_release_wait(key):
    if key == keyboard.Key.esc:
        print('{0} released'.format(key))
        return False

def esperar_esc():
    with keyboard.Listener(
            on_press=main.on_press,
            on_release=main.on_release_wait) as listener:
        listener.join()

#listener = keyboard.Listener(
#    on_press=on_press,
#    on_release=on_release)
#listener.start()
########################################################################################################################

def proc_img(ss):
    global xmg1, xss, andamento
    xss = str(ss)
    os.system("ls ccnc_aux > ccnc_aux/listax.txt")
    # os.system("rm ccnc_aux/img25.jpg")
    # os.system("cp img99.jpg ccnc_aux/img25.jpg")
    andamento = "Analizando as imagens!"
    listax = open(cfg["listax"], "r")

    nomelista = []
    for linha in listax:
        valores = linha.split()
        nomelista.append(valores[0])
    listax.close()
    nlinhas = len(nomelista)

    maxgotas = 0
    ccncgotas = open("grafico.txt", "w")
    for i in range(nlinhas - 2):

        nomearq = "ccnc_aux/" + nomelista[i + 1]

        print(nomearq)
        ngotas = procimg2(nomearq)

        ccncgotas.writelines(str(ngotas))
        ccncgotas.writelines("\n")



        curva[i]=ngotas
        if ngotas > maxgotas:
            maxgotas = ngotas
            nomearqmaxgotas = nomearq

    ccncgotas.close()
    now = datetime.now()
    ccncsai = open(cfg["CCNC_OUT"], "a")
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    str1 = dt_string + " " + str(ss) + " " + str(maxgotas) + "\r"

    ccncsai.writelines(str1)
    ccncsai.close()
    img = cv2.imread(nomearqmaxgotas)

    nomeimg = "{}_{}_{}.jpg".format(dt_string, ss, maxgotas).replace(' ', '_').replace(':', '_').replace('/', '_')
    print(nomeimg)
    xmg1 = maxgotas
    andamento = "Fim da contagem de gotas!"
    print(curva) # no vetor curva temos todas as contagens agora é só plotar
    soma = sum(curva)
    media = soma / 100
    print(media)
    #arqlist = open('/home/lim02/ccnc_v2/ciclo1%/curva', "w")
    #arqlist.write('curva' + '\n', curva)

##########################################################################
    #região de análise do laser demarcada

    for x in range(10,630):
        img[206, x]= (255, 255, 255)
        img[262, x]= (255, 255, 255)

    for y in range(206,262):
        img[y,10]= (255, 255, 255)
        img[y,630]= (255, 255, 255)
#################################################################################
    # região para encontrar o thr médio demarcada
    # for x in range(50,400):
    #     img[140, x]= (255, 255, 255)
    #     img[180, x]= (255, 255, 255)
    #
    # for y in range(140,180):
    #     img[y,50]= (255, 255, 255)
    #     img[y,400]= (255, 255, 255)

    cv2.imwrite('/home/lim02/ccnc_v2/imagensmax/'+nomeimg,img)

########################################################################################################################

def procimg2(nome):
    # print("rotina de processamento de lista de imagens")
    img = cv2.imread(nome)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    alpha = 1.5  # Contrast control (1.0-3.0)
    beta = 0  # Brightness control (0-100)
    gray2 = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)

    p = 0
    z = 0
    for x in range(0, IWD - 1):
        for y in range(IH1_thr, IH2_thr):  # (140,180)
            p = p + gray2[y][x]
            z = z + 1
    thr = int(p / z)
    #print(thr)

    gray3 = gray2[IH1:IH2, IW1:IW2]

    nl = np.size(gray3, 0)
    nc = np.size(gray3, 1)

    for x in range(0, nc):  # transforma para BW com THR+50
        for y in range(0, nl):
            p = gray3[y][x]
            if p < thr + 50:
                gray3[y][x] = 0
            else:
                gray3[y][x] = 255

    thresh = gray3
    kernel = np.ones((3, 3), np.uint8)
    sure_bg = cv2.dilate(thresh, kernel, iterations=1)
    dist_transform = cv2.distanceTransform(sure_bg, cv2.DIST_L1, 5)

    ret, sure_fg = cv2.threshold(dist_transform, 0.7 * dist_transform.max(), 255, 0)
    sure_fg = np.uint8(sure_fg)
    unknown = cv2.subtract(sure_bg, sure_fg)

    ret, markers = cv2.connectedComponents(sure_bg)
    # ret, markers2 = cv.connectedComponents(thresh)
    # ret3, markers3 = cv.connectedComponents(unknown)
    # markers = markers + 1

    ngotas = np.max(markers)
    print(ngotas)

    # if(nome=="/home/lim02/ccnc_v2/imagensmax/29_07_2022_11_34_01_1.0_62.jpg"):
    #     cv2.imshow('Color image', sure_bg) #fgmp
    #     print(markers)  # fgmp
    #     #print(markers2)  # fgmp
    #     #print(markers3)  # fgmp
    #     #cv2.imshow('Color image', unknown3)  # fgmp
    #     print("////////////////////")
    #     print(ngotas)
    #     print("////////////////////")

    return (ngotas)

########################################################################################################################


# Captura imagem da câmera com prarâmetro pré fixados
# def abre_porta_serial():
#     comport = serial.Serial('/dev/ttyACM0', 38400, timeout=5)
#     comport.reset_output_buffer()
#     return(comport)

def proc_imagem():
    print("rotina de processamento de lista de imagens")


def captura_imagem():
    global cap
    #main.cap = cv2.VideoCapture(0)  # 0 Para câmera externa e 1 para câmera interna.
    #    cap = cv2.VideoCapture(0)  # 0 Para câmera externa e 1 para câmera interna.
    cap.set(cv2.CAP_PROP_BRIGHTNESS, 128)
    cap.set(cv2.CAP_PROP_CONTRAST, 128)
    cap.set(cv2.CAP_PROP_SATURATION, 128)
    cap.set(cv2.CAP_PROP_HUE, 128)
    cap.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, 0)
    cap.set(cv2.CAP_PROP_WHITE_BALANCE_RED_V, 0)
    return_value, image = cap.read()
    cv2.imwrite('Aux/imgaux.jpg', image)
    sleep(1)
    cv2.imshow('Color image', image)
    cv2.destroyAllWindows()
    del cap


#######################################################################################################################

def inicializa():
    global BW
    global bw_antigo
    global bw_atual
    global bw_soma
    for y in range(IHD):
        for x in range(IWD):
            BW[x][y] = 0
            bw_antigo[x][y] = 0
            bw_atual[x][y] = 0
            bw_soma[x][y] = 0

#######################################################################################################################
def escrever_json():
    with open('/home/lim02/ccnc_v2/ccnc.cfg', 'w') as f:
        json.dump(cfg,f,indent = 6)

#######################################################################################################################

def le_config(show_config=True):
    """ Configura variaveis baseadas no arquivo de configuracao.

    :param show_config: Mostra configuracao no terminal
    :return:
    """
    global IWD, IHD, IH1, IH2, IW1, IW2, IHDM, IWDM, IH1_thr, IH2_thr,relacao_pm,altura,comprimento_laser,thrfinal
    IWD = cfg["IWD"]  # 640
    IHD = cfg["IHD"]  # 480
    IH1 = cfg["IH1"]  # 206
    IH2 = cfg["IH2"]  # 262
    IW1 = cfg["IW1"]  # 11
    IW2 = cfg["IW2"]  # 630
    relacao_pm = cfg["relacao_pm"]
    altura = cfg["altura"]
    comprimento_laser=cfg["comprimento_laser"]
    thrfinal = cfg["thrfinal"]
    IHDM = int(IHD / 2)
    IWDM = int(IWD / 2)
    IH1_thr = cfg["IH1_thr"]  # 140
    IH2_thr = cfg["IH2_thr"]  # 180
    if show_config:
        print(json.dumps(cfg, indent=4))

#######################################################################################################################

def determina_thr(): #thr de uma regiao quadrada
    global andamento
    andamento = "Remova o calibrador, feche a câmara e precione ESC!"
    print('Remova o calibrador e feche a câmara e precione ESC!')
    esperar_esc()
    # try:
    #     cap = cv2.VideoCapture(0)  # 0 Para câmera externa e 1 para câmera interna.
    #     print("Camera 0")
    # except:
    #     cap = cv2.VideoCapture(1)
    #     print("Camera 1")

    cap.set(cv2.CAP_PROP_BRIGHTNESS, 128)
    cap.set(cv2.CAP_PROP_CONTRAST, 128)
    cap.set(cv2.CAP_PROP_SATURATION, 128)
    cap.set(cv2.CAP_PROP_HUE, 128)
    cap.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, 0)
    cap.set(cv2.CAP_PROP_WHITE_BALANCE_RED_V, 0)
    return_value, image = cap.read()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    alpha = 1.5  # Contrast control (1.0-3.0)
    beta = 0  # Brightness control (0-100)
    gray2 = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)

    p = 0
    z = 0
    for x in range(0, IWD - 1):
        for y in range(IH1_thr, IH2_thr):  # (140,180)
            p = p + gray2[y][x]
            z = z + 1
    thr = int(p / z)
    print("************")
    print(thr)
    cfg["thrfinal"]=thr
    escrever_json()

    return(thr)

#######################################################################################################################

def sobrepor_fotos(thr):
    global andamento
    andamento = "Sobrepondo as imagens!"

    imga = cv2.imread("/home/lim02/ccnc_v2/imagens_calibracao/img0.jpg")
    gray = cv2.cvtColor(imga, cv2.COLOR_BGR2GRAY)
    (thresh, imgb) = cv2.threshold(gray, thr, 255, cv2.THRESH_BINARY)
    listax = open("/home/lim02/ccnc_v2/imagens_calibracao/lista.txt", "r")
    n = 0
    for linha in listax:
        n = n + 1
        valores = linha.split()
        nome = ("/home/lim02/ccnc_v2/imagens_calibracao/" + valores[0])
        img1 = cv2.imread(nome)
        gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        (thresh, img2) = cv2.threshold(gray, thr, 255, cv2.THRESH_BINARY)

        imgb = cv2.bitwise_or(img2, imgb)
    # cv2.imshow("asdasd", imgb)
    laserx = [0 for y in range(IHD)]
    for l in range(100, 300):
        for c in range(IWD):
            laserx[l] = laserx[l] + imgb[l, c]
    maxl = max(laserx) - max(laserx) * 30 / 100
    x = laserx[0]
    i = 100
    while (x < maxl):
        x = laserx[i]
        i = i + 1
    altura1 = i

    while (x > maxl):
        x = laserx[i]
        i = i + 1

    altura2 = i

    print(altura1)
    print(altura2)
    cfg["altura"] = altura2 - altura1
    print(cfg["altura"])

    cfg["IH1"] = altura1
    cfg["IH2"] = altura2
    escrever_json()

    # plt.imshow(imgb)
    # plt.title('imagem sobreposta com 100 imagens')
    # plt.xlabel("pixel")
    # plt.ylabel("pixel")
    #
    # plt.figure()
    # plt.plot(laserx)
    # plt.title('histograma das imagens sobreposta com 100 imagens')
    # plt.xlabel("pixel")
    # plt.ylabel("pixel iluminado em cada linha")
    # plt.show()
    # print(maxl)
    andamento = "Calibração concluida!"

#######################################################################################################################

def determina_altura():
    thr=determina_thr() # valor médio do preto
    ciclo_100_fotos()
    sobrepor_fotos(thr)

#######################################################################################################################

def define_bg():
    """Determina o valor de pixel apagado

    Este valor determina o threshold para o processamento da imagem
    """

    captura_imagem()
    img1 = Image.open('Aux/imgaux.jpg').convert("L")
    img1.show()
    i = 0
    p = []
    for l in range(220, 260):
        for c in range(300, 340):
            p.append(img1.getpixel((c, l)))
    pmax = max(p)
    pmin = min(p)
    pmedio = np.mean(p)
    print(pmedio)


########################################################################################################################

def envia_cmd(comando):
    try:
        comport.reset_output_buffer()
        comport.write(comando.encode())
    except Exception as e:
        pass

########################################################################################################################

def pega_imagem(x):
    img1 = Image.open(x).convert("L")
    threshold = 180
    img2 = img1.point(lambda p: p > threshold and 255)
    # img2.show()
    return (img2)

########################################################################################################################

def transf_bw(img2):
    for y in range(IHD):
        for x in range(IWD):
            if img2.getpixel((x, y)) == 255:
                BW[x][y] = 1
            if img2.getpixel((x, y)) == 0:
                BW[x][y] = 0

    return BW

########################################################################################################################

def bw_final():
    global bw_antigo, img2, bw_atual, bw_soma

    inicializa()
    listax = open("ref/lista.txt", "r")  # TODO: check what is this and put on config file
    nomelista = []
    for linha in listax:
        valores = linha.split()
        nomelista.append(valores[0])
    listax.close()
    narq = len(nomelista)
    for n in range(narq):
        nome_arq = nomelista[n]
        img2 = pega_imagem(nome_arq)
        bw_atual = transf_bw(img2)
        bw_atual[0][0] = 1
        bw_soma = np.add(bw_soma, bw_atual)

    arq_altura = open(cfg["ARQ_ALTURA"], "w")
    for n in range(480):
        n1 = bw_soma[320][n]
        arq_altura.writelines(str(n1) + '\n')
    arq_altura.close()

########################################################################################################################

def bw_incial():
    inicializa()
    listax = open("ref/lista.txt", "r")  # TODO: check what is this and put on config file
    nomelista = []
    for linha in listax:
        valores = linha.split()
        nomelista.append(valores[0])
    listax.close()
    narq = len(nomelista)
    for n in range(narq):
        nome_arq = nomelista[n]
        img2 = pega_imagem(nome_arq)
        bw_atual = transf_bw(img2)
        bw_atual[0][0] = 1
        bw_soma = np.add(bw_soma, bw_atual)

    arq_altura = open(cfg["ARQ_ALTURA"], "w")
    for n in range(480):
        n1 = bw_soma[320][n]
        arq_altura.writelines(str(n1) + '\n')
    arq_altura.close()

    # print(bw_soma)
    # img3 = img2
    # img3.show()

########################################################################################################################

def comprimentolaser():
    nomearq = "Aux/defrel0.jpg"
    img1 = Image.open(nomearq).convert("L")
    img1.show()
    threshold = 180
    img2 = img1.point(lambda p: p > threshold and 255)
    img2.show()
    for y in range(IHD):
        for x in range(IWD):
            BW[x][y] = (img2.getpixel((x, y)))
    coluna = int(IHD / 2)
    linha = 0
    linha1 = 639  # 639 apenas -1, 480 apenas +1
    pixel = 255
    while (pixel == 255):
        # Descobrir primeiro preto
        pixel = BW[linha][coluna]
        linha = linha + 1  # +1 =133 pixeis, -1 = -128 pixeis
        c1 = linha

    while (pixel == 0):
        pixel = BW[linha][coluna]
        linha = linha + 1  # +1 =133 pixeis, -1 = -128 pixeis
        c2 = linha

    while (pixel == 255):
        pixel = BW[linha][coluna]
        linha = linha + 1  # +1 =133 pixeis, -1 = -128 pixeis
        c3 = linha

    while (pixel == 0):
        pixel = BW[linha][coluna]
        linha = linha + 1  # +1 =133 pixeis, -1 = -128 pixeis
        c4 = linha

        p1 = int((c1 + c2) / 2)
        p2 = int((c3 + c4) / 2)
    print(p1)
    print(p2)
    pixellmm = 17
    d = p2 - p1
    rel = d / pixellmm
    print(rel)
    img1.close()

########################################################################################################################
def medida_rel_pixel_mm():
    global andamento
    andamento = "Medindo a relação pixel/mm!"

    BW = [[0 for y in range(IHD)] for x in range(IWD)]
    img = cv2.imread("ref.jpg")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thrantigo=1000
    for x in range(0, int(IWD/2) - 1):
        thr=gray[240][x]
        if (thr<thrantigo):
            thrantigo=thr

    thr=thrantigo+10
    threshold = thr

    img1 = Image.open("ref.jpg").convert("L")
    img2 = img1.point(lambda p: p > threshold and 255)
    for y in range(IHD):
        for x in range(IWD):
            BW[x][y] = (img2.getpixel((x, y)))
    coluna = 0
    linha = int(IHD / 2)
    pixel = 255
    while pixel == 255:
        # Descobrir primeiro preto
        pixel = BW[coluna][linha]
        coluna = coluna + 1  # +1 =133 pixeis, -1 = -128 pixeis
        c1 = coluna

    while pixel == 0:
        pixel = BW[coluna][linha]
        coluna = coluna + 1  # +1 =133 pixeis, -1 = -128 pixeis
        c2 = coluna

    while pixel == 255:
        pixel = BW[coluna][linha]
        coluna = coluna + 1  # +1 =133 pixeis, -1 = -128 pixeis
        c3 = coluna

    while pixel == 0:
        pixel = BW[coluna][linha]
        coluna = coluna + 1  # +1 =133 pixeis, -1 = -128 pixeis
        c4 = coluna

        p1 = int((c1 + c2) / 2)
        p2 = int((c3 + c4) / 2)
    print(p1)
    print(p2)
    cfg["IW1"] = p1
    cfg["IW2"] = p2
    escrever_json()

    cfg["comprimento_laser"] = p2 - p1
    rel = cfg["comprimento_laser"]/cfg["comprimento_padrao_regua"]

    andamento = rel
    cfg["relacao_pm"]=rel
    escrever_json()

    print(rel)
    img1.close()
########################################################################################################################
def ciclo_100_fotos():
    global xmg1
    global dif_temp_x
    global andamento
    global progress
    # try:
    #     cap = cv2.VideoCapture(0)  # 0 Para câmera externa e 1 para câmera interna.
    #     print("Camera 0")
    # except:
    #     cap = cv2.VideoCapture(1)
    #     print("Camera 1")

    cap.set(cv2.CAP_PROP_BRIGHTNESS, 18)
    cap.set(cv2.CAP_PROP_CONTRAST, 128)
    cap.set(cv2.CAP_PROP_SATURATION, 128)
    cap.set(cv2.CAP_PROP_HUE, 128)
    cap.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, 0)
    cap.set(cv2.CAP_PROP_WHITE_BALANCE_RED_V, 0)

    #comport.write(b'J')  # configura para 1% de SS
    sleep(2)
    andamento = "Aguarde a estabilização da temperatura"
    print("Aguarde a estabilização da temperatura")
    sleep(1)

    xmg1 = -99
    dif_temp_x = 0
    comport.write(b'J')  # configura para 1% de SS
    andamento = "Ajustando temperatura!"
    while dif_temp_x < 99:
        print(dif_temp_x)
    andamento = "Produza um ambiente poluido na sala e em seguida precione a tecla ESC!"
    print("Produza um ambiente poluido na sala e em seguida precione a tecla ESC!")
    esperar_esc()

    #print("Produza um ambiente poluido na sala e em seguida precione uma tecla")
    #nome = input()

    comport.write(b'A')  # abre valvula
    sleep(2)
    comport.write(b'L')  # liga bomba
    sleep (10)
    comport.write(b'D')  # deliga bomba
    sleep(2)
    comport.write(b'F')  # fecha valvula
    sleep(2)

    andamento = "Início da retirada das 100 imagens!"

    arqlist = open("/home/lim02/ccnc_v2/imagens_calibracao/lista.txt", "w")
    for i in range(100):
        return_value, image = cap.read()
        # arqlist.write('ccnc_aux/img' + ni + '.jpg' + '\n')
        sleep(0.1)
        cv2.imwrite('/home/lim02/ccnc_v2/imagens_calibracao' + '/img' + str(i) + '.jpg', image)
        arqlist.write('/img' + str(i) + '.jpg' + '\n')
        print('img' + str(i) + '.jpg')
        sleep(0.1)
        progress = i+1
        cv2.destroyAllWindows()
    andamento = "Fim da retirada das 100 imagens!"
    print("Fim da retirada das 100 imagens!")
    arqlist.close()

########################################################################################################################

def tirar_foto_do_calibrador():
    global andamento
    # try:
    #     cap = cv2.VideoCapture(0)  # 0 Para câmera externa e 1 para câmera interna.
    #     print("Camera 0")
    # except:
    #     cap = cv2.VideoCapture(1)
    #     print("Camera 1")
    cap.set(cv2.CAP_PROP_BRIGHTNESS, 0)
    cap.set(cv2.CAP_PROP_CONTRAST, 128)
    cap.set(cv2.CAP_PROP_SATURATION, 128)
    cap.set(cv2.CAP_PROP_HUE, 128)
    cap.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, 0)
    cap.set(cv2.CAP_PROP_WHITE_BALANCE_RED_V, 0)

    andamento = "Abra a câmara, coloque o calibrador e aperte ESC!"

    if cap.isOpened():
        validacao, frame = cap.read()
        while validacao:
            validacao, frame = cap.read()
            cv2.imshow("Video da Webcam", frame)
            key = cv2.waitKey(5)
            if key == 27:
                break
        andamento = "Câmera desligada!"
        sleep(1)
        andamento = "Imagem de referência retirada!"
        print("foto de referência retirada")
        cv2.imwrite("ref.jpg", frame)
        cap.release()
        cv2.destroyAllWindows()

########################################################################################################################

class GTKHandler:
    """ Controle da da interface Grafica (GTK)"""

    def __init__(self, ccnc=None):
        self.cap = None
        self.activity_mode = None
        self.timeout_id = None
        self.progressbar = None
        self.ccnc = ccnc
        super(GTKHandler, self).__init__()

    def on_interface_destroy(self, *args):
        Gtk.main_quit()

    def Ligar_bomba_clicked(self, button=None):
        global andamento
        #print("Ligar Bomba!")
        comport.write(b'L')
        cmd["bomba"] = "L"
        andamento = "Bomba ligada!"
        sleep(1)

    def Desligar_bomba_clicked(self, button=None):
        global andamento
        print("Desligar Bomba!")
        comport.write(b'D')
        cmd["bomba"] = 'D'
        andamento = "Bomba desligada!"
        sleep(1)

    def Abre_valvula_clicked(self, button=None):
        global andamento
        print("Abrir Valvula!")
        comport.write(b'A')
        cmd["valvula"] = 'A'
        andamento = "Valvula aberta!"
        sleep(1)

    def Fecha_valvula_clicked(self, button=None):
        global andamento
        print("Valvula fechada!")
        comport.write(b'F')
        cmd["valvula"] = 'F'
        andamento = "Valvula Fechada!"
        sleep(1)

    def Desligar_SDCC_clicked(self, button=None):
        print("Desligando CCNC")
        exit(0)

    def stop(self, button=None):
        global andamento
        andamento = "Processo encerrado!"
        exit(0)

    def start_single(self, button=None):
        global andamento
        andamento="iniciando medição ciclo unico!"
        #print("iniciando medição ciclo unico")
        sleep(2)
        cmd["ccnc"] = 'K'
        self.ciclo_ss(button)

    def start_burst(self, button=None):
        global andamento
        andamento = "iniciando medição de vários ciclos"
        sleep(2)
        cmd["ccnc"] = 'K'
        ligado = True
        while ligado:
            self.ciclo_ss(button)
            andamento = "############ Iniciando nova sequência ############"
            #print("############ Iniciando nova sequência ############")

    ########################################################################################################################

    def on_timeout(self, user_data):
        """
        Update value on the progress bar
        """
        if self.activity_mode:
            self.progressbar.pulse()
        else:
            new_value = self.progressbar.get_fraction() + 0.01

            if new_value > 1:
                new_value = 0

            self.progressbar.set_fraction(new_value)

        # As this is a timeout function, return True so that it
        # continues to get called
        return True
    ########################################################################################################################
    # saturação

    def tb_cb01(self, button=None):
        global andamento
        cmd["ss01_ck"] = button.get_active()
        if cmd["ss01_ck"] == True:
            andamento = "Super saturação de 0.1% escolhida!"
            #print("super saturação de 0.1%")
            lss[0] = True
        else:
            lss[0] = False

    def tb_cb02(self, button=None):
        global andamento
        cmd["ss02_ck"] = button.get_active()
        if cmd["ss02_ck"] == True:
            andamento = "Super saturação de 0.2% escolhida!"
            #print("super saturação de 0.2%")
            lss[1] = True
        else:
            lss[1] = False

    def tb_cb03(self, button=None):
        global andamento
        cmd["ss03_ck"] = button.get_active()
        if cmd["ss03_ck"] == True:
            andamento = "Super saturação de 0.3% escolhida!"
            #print("super saturação de 0.3%")
            lss[2] = True
        else:
            lss[2] = False

    def tb_cb04(self, button=None):
        global andamento
        cmd["ss04_ck"] = button.get_active()
        if cmd["ss04_ck"] == True:
            andamento = "Super saturação de 0.4% escolhida!"
            #print("super saturação de 0.4%")
            lss[3] = True
        else:
            lss[3] = False

    def tb_cb05(self, button=None):
        global andamento
        cmd["ss05_ck"] = button.get_active()
        if cmd["ss05_ck"] == True:
            andamento = "Super saturação de 0.5% escolhida!"
            #print("super saturação de 0.5%")
            lss[4] = True
        else:
            lss[4] = False

    def tb_cb06(self, button=None):
        global andamento
        cmd["ss06_ck"] = button.get_active()
        if cmd["ss06_ck"] == True:
            andamento = "Super saturação de 0.6% escolhida!"
            #print("Super saturação de 0.6%")
            lss[5] = True
        else:
            lss[5] = False

    def tb_cb07(self, button=None):
        global andamento
        cmd["ss07_ck"] = button.get_active()
        if cmd["ss07_ck"] == True:
            andamento = "Super saturação de 0.7% escolhida!"
            #print("super saturação de 0.7%")
            lss[6] = True
        else:
            lss[6] = False

    def tb_cb08(self, button=None):
        global andamento
        cmd["ss08_ck"] = button.get_active()
        if cmd["ss08_ck"] == True:
            andamento = "Super saturação de 0.8% escolhida!"
            #print("super saturação de 0.8%")
            lss[7] = True
        else:
            lss[7] = False

    def tb_cb09(self, button=None):
        global andamento
        cmd["ss09_ck"] = button.get_active()
        if cmd["ss09_ck"] == True:
            andamento = "Super saturação de 0.9% escolhida!"
            #print("super saturação de 0.9%")
            lss[8] = True
        else:
            lss[8] = False

    def tb_cb10(self, button=None):
        global andamento
        cmd["ss10_ck"] = button.get_active()
        if cmd["ss10_ck"] == True:
            andamento = "Super saturação de 1.0% escolhida!"
            #print("super saturação de 1.0%")
            lss[9] = True
        else:
            lss[9] = False

    ###################################################################################################################
    # calibração

    def calibrar(self, button=None):
        #tirar_foto_do_calibrador()
        threading.Thread(target=self.calibrar_func, daemon=True).start()

    def calibrar_func(self):
        global andamento
        andamento = "Iniciar calibração"
        sleep(2)
        medida_rel_pixel_mm()
        #print('Remova o calibrador e feche a câmara e precione uma tecla')
        #nome = input()
        determina_altura()
    ###################################################################################################################
    # resetar temperatura
    def reset_temp(self, button=None):
        print("resetar diferença de temperatura")
        cmd["reiniciar_temp"] = 'P'

    ###################################################################################################################
    # gráficos
    def sobreposicao(self, button=None):
        print("sobrepor")
        #plt.ylim(0,60)
        tempo = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 5, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 7, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 8, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 9, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.9]
        g=[]
        g1=[]
        g2=[]
        g3=[]
        g4=[]
        g5=[]
        g6=[]
        g7=[]
        g8=[]
        g9=[]
        media=[]
        concentração=[]
        for linha in open('/home/lim02/ccnc_v2/grafico.txt', 'r'):
            dados = [float(s) for s in linha.split()]
            g.append(dados[0])
        for linha in open('/home/lim02/ccnc_v2/grafico1.txt', 'r'):
            dados = [float(s) for s in linha.split()]
            g1.append(dados[0])
        for linha in open('/home/lim02/ccnc_v2/grafico2.txt', 'r'):
            dados = [float(s) for s in linha.split()]
            g2.append(dados[0])
        for linha in open('/home/lim02/ccnc_v2/grafico3.txt', 'r'):
            dados = [float(s) for s in linha.split()]
            g3.append(dados[0])
        for linha in open('/home/lim02/ccnc_v2/grafico4.txt', 'r'):
            dados = [float(s) for s in linha.split()]
            g4.append(dados[0])
        for linha in open('/home/lim02/ccnc_v2/grafico5.txt', 'r'):
            dados = [float(s) for s in linha.split()]
            g5.append(dados[0])
        for linha in open('/home/lim02/ccnc_v2/grafico6.txt', 'r'):
            dados = [float(s) for s in linha.split()]
            g6.append(dados[0])
        for linha in open('/home/lim02/ccnc_v2/grafico7.txt', 'r'):
            dados = [float(s) for s in linha.split()]
            g7.append(dados[0])
        for linha in open('/home/lim02/ccnc_v2/grafico8.txt', 'r'):
            dados = [float(s) for s in linha.split()]
            g8.append(dados[0])
        for linha in open('/home/lim02/ccnc_v2/grafico9.txt', 'r'):
            dados = [float(s) for s in linha.split()]
            g9.append(dados[0])
        for linha in open('/home/lim02/ccnc_v2/graficos/media.txt', 'r'):
            dados = [float(s) for s in linha.split()]
            media.append(dados[0])
        for linha in open('/home/lim02/ccnc_v2/graficos/concentração.txt', 'r'):
            dados = [float(s) for s in linha.split()]
            concentração.append(dados[0])

        # plt.plot(tempo, g)
        # plt.plot(tempo, g1)
        # plt.plot(tempo, g2)
        # plt.plot(tempo, g3)
        # plt.plot(tempo, g4)
        # plt.plot(tempo, g5)
        # plt.plot(tempo, g6)
        # plt.plot(tempo, g7)
        # plt.plot(tempo, g8)
        # plt.plot(tempo, g9)
        #plt.plot(tempo, media, label='Média')
        plt.plot(tempo, concentração, label='Concentração')
        #plt.title('Média das gotas com SS 1%', fontsize=15)
        #plt.title('Curva de gotas com SS 1%', fontsize=15)
        plt.title('Concentração média das gotas com SS 1%', fontsize=15)
        plt.ylabel('Concentração de gotas / cm³', fontsize=13)
        plt.xlabel('Tempo (segundos)', fontsize=13)
        #plt.ylabel('Número de gotas', fontsize=13)
        plt.legend()
        plt.show()
        #a = [31, 26, 25, 28, 27, 25, 25, 22, 23, 22, 21, 22, 16, 14, 15, 15, 19, 21, 20, 20, 18, 19, 15, 13, 9, 10, 12, 13, 8, 8, 10, 11, 12, 13, 12, 8, 7, 6, 9, 9, 9, 7, 6, 6, 8, 9, 8, 8, 9, 10, 10, 12, 12, 10, 9, 8, 10, 10, 8, 10, 9, 9, 11, 11, 11, 7, 6, 8, 7, 6, 5, 4, 3, 3, 1, 1, 3, 3, 3, 3, 5, 6, 8, 10, 8, 9, 8, 8, 8, 7, 7, 7, 4, 3, 3, 3, 4, 3, 2, 0]
        #maxgotas= [43, 30, 66, 45,60,70,67,66,53,53,47,50,51,49,53,55,56,49,45,44,52,45,42,55,52,48,49,46,58,47,46,48,45,38,40,46,37,44,50,46,36,53,46,55,36,35,46,43,33,39,40,36,44,38,39,30,21,36,36,28,42,40,37,36,33,46,42,37,37,43,34,27,30,31,28,31,29,32,27,20,33,30,38,31,33,33,30,22,28,22,25,40,37,42,32,22,32,34,29,28]
        #media = [15.57, 17.21, 19.12, 16.7, 22.82, 29.56, 28.89, 36.55, 31.7, 34.79, 32.52, 32.53, 31.69, 30.0, 33.01, 33.63, 31.47, 29.55, 28.12, 27.49, 25.73, 15.85, 25.72, 29.54, 29.65, 30.23, 25.85, 27.08, 24.04, 26.65, 25.89, 26.19, 23.85, 21.76, 15.24, 19.77, 16.53, 19.47, 20.46, 14.33, 13.15, 17.59, 15.51, 18.71, 10.84, 14.13, 14.02, 19.1, 13.84, 15.02, 17.51, 10.71, 12.6, 15.28, 15.51, 10.94, 8.98, 13.35, 14.41, 12.53, 15.05, 14.11, 13.17, 13.73, 13.23, 14.83, 12.25, 11.29, 15.34, 13.39, 15.7, 9.82, 15.43, 14.2, 12.09, 12.92, 8.8, 10.07, 8.56, 21.65, 19.81, 18.18, 20.56, 21.94, 20.96, 16.67, 15.65, 16.77, 13.98, 13.19, 24.47, 22.44, 22.72, 18.17, 14.74, 13.7, 19.04, 12.82, 12.05, 12.05 ]
        #plt.plot(tempo, maxgotas, color='Orange', label = 'SS 1%')
        #plt.plot(tempo, media, color='Blue', label = 'média')
        #plt.plot(tempo, a, color='red', label = 'SS 0.5%')
        #plt.plot(tempo, d, color='Green', label = 'SS 0.8%')
        #plt.plot(tempo, e, color='Purple', label = 'SS 1%')
        # plt.plot(tempo, curva6, color='Orange')
        # plt.plot(tempo, curva7, color='Blue')
        # plt.plot(tempo, curva8, color='red')
        # plt.plot(tempo, curva9, color='Green')
        # plt.plot(tempo, curva10, color='Purple')

    ###################################################################################################################

    def Histograma(self, button=None):
        imga = cv2.imread("/home/lim02/ccnc_v2_29_julho_2022/imagens_calibracao/img0.jpg")
        gray = cv2.cvtColor(imga, cv2.COLOR_BGR2GRAY)
        (thresh, imgb) = cv2.threshold(gray, cfg["thrfinal"], 255, cv2.THRESH_BINARY)
        listax = open("/home/lim02/ccnc_v2_29_julho_2022/imagens_calibracao/lista.txt", "r")
        n = 0
        for linha in listax:
            n = n + 1
            valores = linha.split()
            nome = ("/home/lim02/ccnc_v2_29_julho_2022/imagens_calibracao/" + valores[0])
            img1 = cv2.imread(nome)
            gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            (thresh, img2) = cv2.threshold(gray, cfg["thrfinal"], 255, cv2.THRESH_BINARY)

            imgb = cv2.bitwise_or(img2, imgb)
        # cv2.imshow("asdasd", imgb)
        laserx = [0 for y in range(IHD)]
        for l in range(100, 300):
            for c in range(IWD):
                laserx[l] = laserx[l] + imgb[l, c]
        maxl = max(laserx) - max(laserx) * 30 / 100
        x = laserx[0]
        i = 100
        while (x < maxl):
            x = laserx[i]
            i = i + 1
        altura1 = i

        while (x > maxl):
            x = laserx[i]
            i = i + 1

        altura2 = i

        print(altura1)
        print(altura2)
        cfg["altura"] = altura2 - altura1
        print(cfg["altura"])

        cfg["IH1"] = altura1
        cfg["IH2"] = altura2
        escrever_json()

        plt.imshow(imgb)

        plt.title('Sobreposição com 100 imagens')
        x=[10,630]
        y=[206,206]
        x1=[10,630]
        y1=[262,262]
        x2=[10,10]
        y2=[206,262]
        x3=[630,630]
        y3=[206,262]
        #plt.text(330, 206, "206", color="black", fontsize=15)
        #plt.text(330, 261, "261", color="black", fontsize=15)
        plt.plot(x,y,x1,y1,x2,y2,x3,y3, color="white", linewidth=3)
        plt.xlabel("Pixel")
        plt.ylabel("Pixel")

        plt.figure()
        plt.plot(laserx)
        plt.title('Gráfico das imagens sobrepostas com 100 imagens')
        plt.plot(206, 68600, marker='.', color="red")
        plt.plot(261, 68600, marker='.', color="red")
        plt.text(207, 68600, "206")
        plt.text(262, 68600, "262")
        plt.xlabel("Pixel")
        plt.ylabel("Pixel iluminado em cada linha")
        plt.show()
        print(maxl)

    ###################################################################################################################
    #média

    def Media(self, button=None):
        print("média")
        curva1 = [15, 14, 14, 14, 14, 15, 15, 15, 16, 15, 15, 14, 14, 14, 13, 12, 11, 11, 12, 12, 12, 10, 11, 10, 10, 11, 11, 10, 10, 9, 10, 9, 10, 10, 9, 9, 10, 9, 7, 8, 8, 8, 7, 7, 7, 8, 9, 8, 9, 7, 7, 9, 9, 9, 9, 11, 11, 11, 12, 12, 11, 11, 11, 11, 10, 10, 10, 10, 10, 10, 9, 9, 8, 7, 8, 6, 6, 6, 7, 6, 6, 6, 6, 6, 7, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 0]
        soma = np.mean(curva1)
        x=[0,10]
        y=[10,10]
        plt.plot(tempo, curva1)
        plt.plot(x,y, marker='.', color="red")
        plt.show()

    ###################################################################################################################
    # camera

    def rel_pix_mm(self, button=None):
        captura_imagem()
        medida_rel_pixel_mm()
        bw_incial()

    def press_esc(self, key):
        if key == keyboard.Key.esc:
            self.esc_pressed=1

    def mostra_camera(self, button=None):
        global andamento

        andamento = "Câmera ligada!"
        print("Câmera ligada!")
        cap.set(cv2.CAP_PROP_BRIGHTNESS, 128)
        cap.set(cv2.CAP_PROP_CONTRAST, 128)
        cap.set(cv2.CAP_PROP_SATURATION, 128)
        cap.set(cv2.CAP_PROP_HUE, 128)
        cap.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, 0)
        cap.set(cv2.CAP_PROP_WHITE_BALANCE_RED_V, 0)

        #cap = cv2.VideoCapture(0)

        if cap.isOpened():
            validacao, frame = cap.read()
            while validacao:
                validacao, frame = cap.read()
                cv2.imshow("Video da Webcam", frame)
                key = cv2.waitKey(5)
                if key == 27:  # ESC
                    break
            andamento = "Câmera desligada!"
            print("foto de referência retirada")
            cv2.imwrite("ref.jpg", frame)

        cap.release()
        cv2.destroyAllWindows()

    ###################################################################################################################

    # ciclo para análise da super saturação

    def ciclo_ss(self, button=None):
        threading.Thread(target=self.ciclo_ss_func, daemon=True).start()

    def ciclo_ss_func(self):
        global xmg1
        global xss
        global dif_temp_x
        global andamento
        global progress

        print("##### Início de ciclo #####")
        andamento = "##### Início de ciclo #####"
        progress = 0
        sleep(3)

        for j in range(10):
            dif_temp_x = 0
            if lss[j] == True:
                envia_cmd(cmd_ss[j])
                print(j, lss[j])
                if j == 0:
                    ss = 0.1
                elif j == 1:
                    ss = 0.2
                elif j == 2:
                    ss = 0.3
                elif j == 3:
                    ss = 0.4
                elif j == 4:
                    ss = 0.5
                elif j == 5:
                    ss = 0.6
                elif j == 6:
                    ss = 0.7
                elif j == 7:
                    ss = 0.8
                elif j == 8:
                    ss = 0.9
                elif j == 9:
                    ss = 1.0

                xss=ss
                xmg1=-99
                andamento ="Ajustando temperatura!"
                while dif_temp_x <99:
                    print(dif_temp_x)
                arqlist = open(cfg["listax"], "w")   #arqlist = open("ccnc_aux/lista.txt", "w")
                sleep(1)
                #print("##### Início de ciclo #####")
                self.Abre_valvula_clicked()
                sleep(1)
                self.Ligar_bomba_clicked()
                sleep(10)
                self.Desligar_bomba_clicked()
                self.Fecha_valvula_clicked()
                sleep(1)

                #sleep(3)

                andamento="inicio da gravação das imagens!"
                #print("inicio da gravação das imagens 2")
                for i in range(100):
                    if (i<10):
                        ni="0"+str(i)
                    if(i>9):
                        ni=str(i)
                    return_value, image = cap.read()
                    nome_arq_img=cfg["dir_img"]+ni+'.jpj'
                    # cv2.imwrite('ccnc_aux/img' + ni + '.jpg', image)
                    cv2.imwrite(cfg["dir_img"]+'/img' + ni + '.jpg', image)
                    # arqlist.write('ccnc_aux/img' + ni + '.jpg' + '\n')
                    arqlist.write(cfg["dir_img"]+'/img' + ni + '.jpg' + '\n')
                    sleep(0.1)
                    progress = i+1
                andamento = "Fim da gravação das imagens!"
                #print("fim da gravação das imagens 2")
                cv2.destroyAllWindows()
                arqlist.close()
                sleep(1)
                progress = 0
                proc_img(ss)
                progress = 100
                andamento = "Fim do ciclo!"
                sleep(5)
            #sleep(2)
        andamento = "Processo concluido!"
        #print("Fim do ciclo SS")

########################################################################################################################
# parametro de mensuração

class CCNC_SDCC(Thread):
    global xmg1

    def __init__(self, tup=None, tbp=None, tdif=None, super_sat=None, ndrops=None, concentration=None, n_frames=None, processo=None, exemplo=None, progressbar=None, items=None):
        self.tup = tup
        self.tbp = tbp
        self.tdif = tdif
        self.super_sat = super_sat
        self.ndrops = ndrops
        self.concentration = concentration
        self.n_frames = n_frames
        self.processo = processo
        self.exemplo = exemplo
        self.progressbar = progressbar
        self.items = items
        self.bomba = 'D'
        self.valvula = 'F'
        # self.singlebust = 'F'
        self.set_ss10 = False
        self.val = None
        super(CCNC_SDCC, self).__init__()

    def set_tup(self, tup):
        self.tup = tup

    def get_tup(self):
        return self.tup

    def set_tbp(self, tbp):
        self.tbp = tbp

    def get_tbp(self):
        return self.tbp

    def set_tdif(self, tdif):
        self.tdif = tdif

    def get_tdif(self):
        return self.tdif

    def set_super_sat(self, super_sat):
        self.super_sat = super_sat

    def get_super_sat(self):
        return self.super_sat

    def set_ndrops(self, ndrops):
        self.ndrops = ndrops

    def get_ndrops(self):
        return self.ndrops

    def set_concentration(self, concentration):
        self.concentration = concentration

    def get_concentration(self):
        return self.concentration

    def set_n_frames(self, n_frames):
        self.n_frames = n_frames

    def get_n_frames(self):
        return self.n_frames

    def set_processo(self, processo):
        self.processo = processo

    def get_processo(self):
        return self.processo

    def set_exemplo(self, exemplo):
        self.exemplo = exemplo

    def get_exemplo(self):
        return self.exemplo

    def set_progressbar(self, progressbar):
        self.progressbar = progressbar

    def get_progressbar(self):
        return self.progressbar

    def set_items(self, items):
        self.items = items

    def get_items(self):
        return self.items

    def set_ss10(self, val):  # fgmp
        self.val = val

    def run(self) -> None:
        global dif_temp_x
        # cap = cv2.VideoCapture(0)
        while True:
            sleep(1)
            # print("executando thred principal")
            if cmd["ccnc"] == 'K':
                cmd["ccnc"] = 'X'
            if cmd["bomba"] == 'L':
                comport.write(b'L')
                cmd["bomba"] = 0
            if cmd["bomba"] == 'D':
                comport.write(b'D')
                cmd["bomba"] = 0
            if cmd["valvula"] == 'A':
                comport.write(b'A')
                cmd["valvula"] = 0
            if cmd["valvula"] == 'F':
                comport.write(b'F')
                cmd["valvula"] = 0
            if cmd["ss01_ck"] == 'E':
                comport.write(b'E')
                cmd["ss01_ck"] = 0
            if cmd["ss02_ck"] == 'H':
                comport.write(b'H')
                cmd["ss02_ck"] = 0
            if cmd["ss03_ck"] == 'Z':
                comport.write(b'Z')
                cmd["ss03_ck"] = 0
            if cmd["ss04_ck"] == 'V':
                comport.write(b'V')
                cmd["ss04_ck"] = 0
            if cmd["ss05_ck"] == 'M':
                comport.write(b'M')
                cmd["ss05_ck"] = 0
            if cmd["ss06_ck"] == 'N':
                comport.write(b'N')
                cmd["ss06_ck"] = 0
            if cmd["ss07_ck"] == 'Y':
                comport.write(b'Y')
                cmd["ss07_ck"] = 0
            if cmd["ss08_ck"] == 'I':
                comport.write(b'I')
                cmd["ss08_ck"] = 0
            if cmd["ss09_ck"] == 'O':
                comport.write(b'O')
                cmd["ss09_ck"] = 0
            if cmd["ss10_ck"] == 'J':
                comport.write(b'J')
                cmd["ss10_ck"] = 0

            time.sleep(1)
            envia_cmd('S')
            #if main.STOP_PROGRAM == 1:
            #    print('ESC pressed. stopping')
            #    Gtk.main_quit()
            #    return

            try:
                comport.reset_input_buffer()
                VALUE_SERIAL = comport.readline().decode().split()
                print(" ".join(VALUE_SERIAL))
                texto1 = VALUE_SERIAL[0]
                texto2 = VALUE_SERIAL[1]
                texto3 = VALUE_SERIAL[2]

                dif_temp_x = float(texto3)

                GLib.idle_add(self.tup.set_text, texto1)
                GLib.idle_add(self.tbp.set_text, texto2)
                GLib.idle_add(self.tdif.set_text, texto3)
                # self.tup.set_text(texto1)
                # self.tbp.set_text(texto2)
                # self.tdif.set_text(texto3)
                # self.super_sat.set_text(texto4)

                # self.concentration.set_text(texto6)
                # self.n_frames.set_text(texto7)
            except Exception as e:
                pass
            GLib.idle_add(self.super_sat.set_text, str(xss))
            if(xmg1==-99):
                strmg1="--"
            else:
                strmg1 = str(xmg1)

            GLib.idle_add(self.ndrops.set_text, strmg1)

            GLib.idle_add(self.processo.set_text, andamento)

            GLib.idle_add(self.exemplo.set_label, foto)

            GLib.idle_add(self.progressbar.set_fraction, progress/100)

            #GLib.idle_add(self.items.set_sensitive(True), spinner)

            #GLib.idle_add(self.items.set_stop, spinner)
            # self.super_sat.set_text(xss)
            # self.ndrops.set_text(str(xmg1))
            #print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

########################################################################################################################
if __name__ == '__main__':
    for i in range(100):
        curva[i]=0
        tempo[i]=0.1*i
    for s in cfg["SERIAL"]:
        try:
            comport = serial.Serial(s, 38400, timeout=5)
            if comport.isOpen():
                break
        except:
            print("Checar serial no arquivo de configuracao.")
            exit(0)
    le_config(show_config=False)

    comport.write(b'D')  # desliga Bomba
    comport.write(b'F')  # fecha a válvula

    xmg1 = -99
    xss = "--"
    andamento = "########################################################################"
    foto = "Template Image"
    progress = 0
    spinner = True

    try:
        cap = cv2.VideoCapture(0)  # 0 Para câmera externa e 1 para câmera interna.
        print("Camera 0")
    except:
        cap = cv2.VideoCapture(1)
        print("Camera 1")

    ss01 = True
    myCCNC = CCNC_SDCC()
    myHandler = GTKHandler(myCCNC)

    builder = Gtk.Builder()
    builder.add_from_file(cfg["INTERFACE_GLADE"])
    builder.connect_signals(myHandler)

    myCCNC.set_tdif(builder.get_object("tdif"))
    myCCNC.set_tbp(builder.get_object("tbp"))
    myCCNC.set_tup(builder.get_object("tup"))
    myCCNC.set_ndrops(builder.get_object("ndrops"))
    myCCNC.set_super_sat(builder.get_object("super_sat"))
    myCCNC.set_processo(builder.get_object("processo"))
    myCCNC.set_exemplo(builder.get_object("exemplo"))
    myCCNC.set_progressbar(builder.get_object("progressbar"))
    myCCNC.set_items(builder.get_object("items"))

    window = builder.get_object("interface")
    window.show_all()

    myCCNC.daemon = True
    myCCNC.start()
    Gtk.main()
