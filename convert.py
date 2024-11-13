'''
2024/10/25-2024/11/6
该模块用于转换miobject格式模型文件数据为我的世界Java版展示实体指令

转换注意事项
1,注意位置偏移和旋转值进行相反处理（每个旋转和位置参数*-1），因为mc和mi中东西默认朝向相反
2.注意由于实际指令只使用left_rotation(只能-180~180度转),故旋转值超过+-180度的处理，数值（欧拉角）先整除360，大于180度的减去360，小于-180的加上360，得到正确旋转值
3.角度转四元数（可用scipy读取）
4.mi里物品的初始位置相较mc里会往上偏移0.5个单位，mi中轴心都在底部，mc在体心
5.同类方块进行颜色和材质分类
6.mi和mc的移动比是16/1 缩放比是1/1（1为标准方块单位）
7.查询字典使用name+variation/color/type作为键值，获得mc内容id
8.miobject是标准json格式文件，可用json模块读取
9.mc指令统一使用物品类实体（即创造背包的内容），因为方块展示实体和物品展示实体轴心不同
10.mi模型参数精确到小数点后5位
11.mi中物体的坐标分为默认坐标和帧坐标，应读取帧坐标（第0帧），故所以模型都应当具备第0帧
12.一段非匀速速度曲线可用多段匀速直线近似表示，而mc中展示实体只能匀速运动
13.mi文件和mi软件中Y与Z轴互换了
15.部分方块在mc中拥有特殊原点位置（如地毯），这些方块直接按同方法转换会出错

召唤一个物品展示实体的实例
单个模型
summon minecraft:item_display ~ ~ ~ {item:{id: "minecraft:dirt", Count: 1},Tags:["a"],transformation:{scale:[1.0f,1.0f,1.0f],translation:[0.0f,0.0f,0.0f],left_rotation:[0.0f,0.0f,0.0f,1.0f],right_rotation:[0.0f,0.0f,0.0f,1.0f]}}
多个模型
summon item_display ~ ~ ~ {Tags:["mapping_model"],Passengers:[{Tags:["j+","mapping_model","k"],id:"minecraft:item_display",item:{Count:1b,id:"minecraft:green_terracotta"},transformation:{left_rotation:[0.0f,0.0f,0.0f,1.0f],right_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.3758f,0.497f,0.3769f],translation:[0.0f,0.2389f,0.0f]}},{Tags:["j+","mapping_model","k"],id:"minecraft:item_display",item:{Count:1b,id:"minecraft:smooth_stone"},transformation:{left_rotation:[0.0f,0.0f,0.0f,1.0f],right_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.175f,0.294f,0.175f],translation:[0.0f,0.537f,0.0f]}},{Tags:["j+","mapping_model","k"],id:"minecraft:item_display",item:{Count:1b,id:"minecraft:lightning_rod"},transformation:{left_rotation:[0.5f,-0.5f,0.5f,0.5f],right_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.4778f,0.4778f,0.4778f],translation:[-0.03f,0.597f,0.0f]}}]}
'''
#导入必需库
import json
import math
import numpy as np
import scipy.linalg as linalg
import sys
import os
import time

'''
# 日志输出
class Logger():
    def __init__(self, filename=os.path.realpath(os.path.dirname(sys.argv[0]))+"Default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    def write(self, message):
        if self.log is not None:
            self.terminal.write(message)
            self.log.write(message)

    def flush(self):
        pass
'''
#欧拉角转旋转矩阵
def rotate_mat(axis, radian):
    rot_matrix = linalg.expm(np.cross(np.eye(3), axis / linalg.norm(axis) * radian))
    return rot_matrix

#原点偏移修正
def offset_correct(roll,pitch,yaw,sca_y):
    #未旋转原点坐标（mc）
    pos = [0,0.5*sca_y,0]
    # 定义x,y和z轴
    axis_x, axis_y, axis_z = [1, 0, 0], [0, 1, 0], [0, 0, 1]
    # 返回x,y,z旋转矩阵
    rot_matrix_x = rotate_mat(axis_x, roll)
    rot_matrix_y = rotate_mat(axis_y, pitch)
    rot_matrix_z = rotate_mat(axis_z, yaw)
    pos_rot = np.dot(rot_matrix_x,pos)
    pos_rot = np.dot(rot_matrix_y, pos_rot)
    pos_rot = np.dot(rot_matrix_z, pos_rot)
    #返回原点偏移值
    return [float(pos_rot[i]) for i in range(3)]

#角度转换适配left_rotation
def angle_convert(angle):
    tmp=angle
    if tmp<0:
        angle = -angle
    angle%=360
    if tmp<0:
        angle = -angle
    if angle > 180:
        return angle - 360
    elif angle < -180:
        return angle + 360
    else:
        return angle

#软件打包资源嵌入后获得正确路径
def get_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.normpath(os.path.join(base_path, relative_path))

#单个mi模型到mc模型的数据格式转换
def transform(mi_unit):
    global log
    #mi_unit格式为[模型类型，模型名字，坐标，旋转，大小]
    with open(get_path("./resource/dictionary.json"),'r') as dictionary:
        dic = json.load(dictionary) #加载词典
        object_type = mi_unit[0];object_name = mi_unit[1];object_pos = mi_unit[2];object_rot = mi_unit[3];object_sca = mi_unit[4] #读取mi模型数据
        mc_pos=[];mc_sca=[] #存储mc坐标值和大小值
        # 获取并转换为mc旋转值（弧度制）
        roll = math.radians(angle_convert(object_rot[0] )) #X
        pitch = math.radians(angle_convert(object_rot[1] +180)) #Y
        yaw = math.radians(angle_convert(object_rot[2] )) #Z
        # id转换
        with open(get_path("./resource/blacklist.txt"),'r') as blacklist: #读取黑名单id
            bk = []
            for line in blacklist:
                bk.append("minecraft:"+line.strip())
            error_list = [[],[]] #存储无法转换的模型id
            if object_type == "block":
                mc_id = "minecraft:" + dic.get(object_name,"NotFound")
                if mc_id in bk:
                    error_list[0].append(mc_id)
                    log+=("\n"+"出现黑名单id：" + mc_id)
                    print("出现黑名单id：" + mc_id)
                    mc_id = "minecraft:barrier"
                elif mc_id == "NotFound":
                    error_list[1].append(mc_id)
                    log += ("\n" + "出现黑名单id：" + mc_id)
                    print("出现非字典id：" + mc_id)
                    mc_id = "minecraft:structure_void"
            else:
                mc_id = "minecraft:"+ object_name

        #坐标转换
        mc_pos.append(str((object_pos[0] / 16 + offset_correct(roll ,math.radians(angle_convert(object_rot[1] )) ,yaw ,object_sca[1])[0]) * (-1))+'f') # x轴
        mc_pos.append(str((object_pos[1] / 16 + offset_correct(roll ,math.radians(angle_convert(object_rot[1] )) ,yaw ,object_sca[1])[1]) )+'f') # y轴
        mc_pos.append(str((object_pos[2] / 16 + offset_correct(roll ,math.radians(angle_convert(object_rot[1] )) ,yaw ,object_sca[1])[2]) * (-1))+'f') # z轴

        #旋转欧拉角转换四元数
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        w = cr *cp * cy - sr * sp * sy
        x = sr *cp * cy + cr * sp * sy
        y = cr *sp * cy - sr * cp * sy
        z = cr *cp * sy + sr * sp * cy
        mc_quaternion = [ str(x)+'f', str(y)+'f', str(z)+'f',str(w)+'f']

        # 大小转换
        for i in object_sca:
            mc_sca.append(str(i)+'f')
    mc_unit = [mc_id,mc_pos,mc_quaternion,mc_sca] #存出单个mc模型数据，格式为[mc中id,坐标，四元数旋转值，大小]
    return mc_unit,error_list

#读取miobject文件数据
def read_miobject(path):
    global log
    log+=("\n"+"miobject模型文件："+path+"\n"+"程序运行时间：" +time.strftime('%Y年%m月%d日%H时%M分%S秒'))
    print("miobject模型文件："+path+"\n"+"程序运行时间：" +time.strftime('%Y年%m月%d日%H时%M分%S秒') + "\n")
    with open(path, 'r') as file:
        object = json.load(file)
        #创立存储各个mi模型数据的列表，单个模型数据单元为[模型类型，模型名字，坐标，旋转，大小]
        object_list= []
        #储存方块模板
        template_dic = {}

        #创建方块模板词典
        log+=("\n"+"<<miobeject文件模型使用模板>>")
        print("<<miobeject文件模型使用模板>>")
        for i in range(len(object["templates"])):
            #获取模板id
            object_id = object["templates"][i]["id"]
            #获取模板类型
            object_type = object["templates"][i]["type"]
            log += ("\n" + "模板-"+object_id+" 模板类型: "+object_type)
            print("模板-"+object_id,"模板类型:",object_type,end='，')
            #获取模板名称
            if object_type == "block":
                object_name = ""
                for j in object["templates"][i]["block"]["state"].keys():
                    if j in ["variant","color","type"]: #设置可以用于键值的特殊state
                        object_name += ("_" + object["templates"][i]["block"]["state"][j] )
                object_name = object["templates"][i]["block"]["name"] + object_name
            else:
                object_name = object["templates"][i]["item"]["name"].split("/")[1]
            log+=("。"+"模板名称: "+object_name)
            print("模板名称:",object_name)
            template_dic[object_id] = [object_type,object_name]
        log+="\n"
        print("\n")

        #获取模型3D数据并整合所有数据，添加到object_list中
        log+=("\n"+"<<miobeject文件所有模型>>")
        print("<<miobeject文件所有模型>>")
        j=0
        for i in object["timelines"]:
            try:
                #不读取文件夹类型
                if i["type"] != "folder":
                    #判断是否有第0帧，若没有则使用默认值
                    if "0" in i["keyframes"].keys():
                        #判断miobject中是否有盖值，若没有则使用默认值
                        object_pos = [i["keyframes"]["0"].get("POS_X",i["default_values"]["POS_X"]),i["keyframes"]["0"].get("POS_Z",i["default_values"]["POS_Z"]),i["keyframes"]["0"].get("POS_Y",i["default_values"]["POS_Y"])]

                        x_r = i["keyframes"]["0"].get("ROT_X",0.0) ; y_r = i["keyframes"]["0"].get("ROT_Z",0.0) ; z_r = i["keyframes"]["0"].get("ROT_Y",0.0)

                        object_rot = [x_r,y_r,z_r]

                        object_sca = [i["keyframes"]["0"].get("SCA_X",1.0),i["keyframes"]["0"].get("SCA_Z",1.0),i["keyframes"]["0"].get("SCA_Y",1.0)]
                    else:
                        object_pos = [i["default_values"]["POS_X"],i["default_values"]["POS_Y"],i["default_values"]["POS_Z"]]

                        object_rot = [0,0,0]

                        object_sca = [1.0,1.0,1.0]
                    #未使用语句
                    #print(path.split("/")[-1]+"模型文件中，ID为",i["id"],"的",str(template_dic[i["temp"]][1])+"模型缺少第0帧，无法正常读取")
                    object_list.append([])
                    object_list[j].append(template_dic[i["temp"]][0])
                    object_list[j].append(template_dic[i["temp"]][1])
                    object_list[j].append(object_pos)
                    object_list[j].append(object_rot)
                    object_list[j].append(object_sca)
                    log+=("\n"+"模型"+ str(j) + "│"+"类型："+object_list[j][0]+" 名称："+object_list[j][1]+" 使用模板："+i["temp"]+"\n"+"坐标： "+str(object_list[j][2])+"\n"+"旋转： "+str(object_list[j][3])+"\n"+"大小： "+str(object_list[j][4])+"\n"+"----------------------------")
                    print("模型"+ str(j) + "│","类型："+object_list[j][0],"名称："+object_list[j][1],"使用模板："+i["temp"])
                    print("坐标：",object_list[j][2])
                    print("旋转：",object_list[j][3])
                    print("大小：",object_list[j][4])
                    print("----------------------------")
                    j+=1
            except :
                return "ERROR_INVALID_FILE"
        return object_list

#将数据转换为mc指令
def to_mc_command(miobject_name,debug=False):
    global log
    id_list = []
    cb_data = []
    log=""
    if debug == True:#开启调试模式，输出日志信息
        path = os.path.abspath(os.path.dirname(__file__))  # 获取当前py文件的父目录
        type = sys.getfilesystemencoding()
        '''
        sys.stdout  = Logger(str(miobject_name.split(".")[0])+'_miobject_log.txt')
        '''
        log+=("\n"+"\n"+"==============================="+"\n"+path+"\n"+os.path.dirname(__file__)+"\n"+'------DEBUG MODE------')
        print("\n"+"===============================")
        print(path)
        print(os.path.dirname(__file__))
        print('------DEBUG MODE------')
    try:
        error_dic = {"bk":[],"nf":[]}
        mi_units = read_miobject(miobject_name)
        if mi_units != "ERROR_INVALID_FILE":
            for unit in mi_units:
                unit_data,unit_error_list = transform(unit)
                id = unit_data[0]
                error_dic["bk"].extend(unit_error_list[0])
                error_dic["nf"].extend(unit_error_list[1])
                #去除列表中每个字符串数据自带的''
                pos = str(unit_data[1]).replace("'","")
                qua = str(unit_data[2]).replace("'", "")
                sca = str(unit_data[3]).replace("'","")
                #拼接重复项
                cb_data.append('''{Tags:["j+","mapping_model","k"],id:"minecraft:item_display",item:{Count:1b,id:"%s"},transformation:{left_rotation:%s,right_rotation:[0.0f,0.0f,0.0f,1.0f],scale:%s,translation:%s}}'''%(id,qua,sca,pos))
                id_list.append(id)
            #组合全部数据成一条指令
            cb = '''/summon item_display ~ ~ ~ {Tags:["mapping_model"],Passengers:['''
            for i in cb_data:
                cb = cb + i + ","
            cb = cb[:-1] + "]}"
            log+=("\n"+"生成指令为："+"\n"+cb+"\n"+"===============================")
            print("\n"+"生成指令为：")
            print(cb)
            print("===============================")
        else:
            log+=("\n"+"ERROR："+miobject_name+"模型文件内容或格式有误，退出程序")
            print("ERROR："+miobject_name+"模型文件内容或格式有误，退出程序")
            return "ERROR_INVALID_FILE",log
    except FileNotFoundError:
        log += ("\n" + "ERROR：找不到"+miobject_name+"模型文件，退出程序")
        print("ERROR：找不到"+miobject_name+"模型文件，退出程序")
        return "ERROR_FILE_NOT_FOUND",log
    return [cb,id_list,error_dic],log
