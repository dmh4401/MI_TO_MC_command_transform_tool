from tkinter import *
from tkinter import ttk
from tkinter import StringVar
from tkinter.scrolledtext import ScrolledText
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
import win32clipboard as wcb
import webbrowser
import convert
import os
import sys

#主界面
root = Tk()
root.title("MTM指令转换工具v1.0.0")
root.geometry("400x420")
root.iconbitmap(convert.get_path("./resource/m.ico"))
root.resizable(False, False)

# 绑定label单击事件
def open_url_MT(event):
    webbrowser.open("https://space.bilibili.com/392374167", new=0)
def open_url_QF(event):
    webbrowser.open("https://space.bilibili.com/3546729406269699", new=0)
def thankyou(event):
    messagebox.showinfo("感谢有你:>", "感谢每一位开放人员的付出，少了你们中的任何一个这个软件都无法完成ヽ(ﾟ∀ﾟ)ﾒ(ﾟ∀ﾟ)ﾉ ")
def open_win_info():
    #关于本软件界面
    win_info = Toplevel(root)
    win_info.title("关于此软件")
    win_info.geometry("255x380")
    win_info.iconbitmap(convert.get_path("./resource/m.ico"))
    win_info.resizable(False, False)

    #分割线
    ttk.Separator(win_info).pack(fill="x", pady=160)

    #标签
    label_photo = Label(win_info, anchor="w", image=photo_mtm)
    label_photo.place(x=35, y=10, width=187, height=123)
    label_title = Label(win_info, text="MI TO MC 指令转换工具", anchor="w", font=("黑体", 15, "bold"))
    label_title.place(x=11, y=100, width=240, height=30)
    label_version = Label(win_info, text="ver 1.0.0", anchor="w")
    label_version.place(x=90, y=140, width=240, height=12)
    #介绍
    label_intro1 = Label(win_info, text="MI TO MC 指令转换工具(MTM)是一个免费", anchor="w")
    label_intro1.place(x=0, y=180, width=260, height=12)
    label_intro2 = Label(win_info, text="开源软件，用于实现miobject模型到生成mc", anchor="w")
    label_intro2.place(x=0, y=200, width=260, height=12)
    label_intro2 = Label(win_info, text="展示实体指令的转换。", anchor="w")
    label_intro2.place(x=0, y=220, width=260, height=12)
    #开发人员名单
    label_creater = Label(win_info, text="=开发人员名单=", anchor="w",font=("黑体", 10,"bold"))
    label_creater.place(x=65, y=260, width=240, height=12)
    label_creater.bind("<Button-1>", thankyou)
    label_CR = Label(win_info, text="超帅气的指令师CR(主要程序设计，编写)", anchor="w",foreground="#0600ff")
    label_CR.place(x=10, y=290, width=240, height=12)
    label_CR.bind("<Button-1>", open_url_CR)
    label_MT = Label(win_info, text="傲彡蠢陌丶小馒头(程序设计，思路提供，测试)", anchor="w",foreground="#0600ff")
    label_MT.place(x=0, y=310, width=260, height=12)
    label_MT.bind("<Button-1>", open_url_MT)
    label_QF = Label(win_info, text="清风不灭v(思路提供)", anchor="w",foreground="#0600ff")
    label_QF.place(x=60, y=330, width=240, height=12)
    label_QF.bind("<Button-1>", open_url_QF)

filename=StringVar()
def open_file():
    filename.set(askopenfilename(title="请选择miobject格式模型文件",filetypes=[("miobject模型文件", "*.miobject")]))
    text_filename.set("当前模型文件："+filename.get().split("/")[-1])
    root.title("MTM："+filename.get())
    print("读入文件 "+ filename.get())

def start_transform():
    if filename.get() !='':
        temp = convert.to_mc_command(filename.get(),cb_debug_var.get())
        result = temp[0]
        log = temp[1]
        if cb_debug_var.get():
            if hasattr(sys, 'frozen'):
                application_path = os.path.dirname(sys.executable)
            elif __file__:
                application_path = os.path.dirname(os.path.abspath(__file__))
            log_output=open(application_path+"\\"+filename.get().split("/")[-1]+'_miobject_log.txt',"a")
            print(application_path+filename.get().split("/")[-1]+'_miobject_log.txt')
            log_output.write(log)
            log_output.close()
        if result == "ERROR_FILE_NOT_FOUND" :
            messagebox.showerror("哎呀呀...", "无法找到此miobject模型，请检查原文件是否被删除或路径是否变更等")
        elif result == "ERROR_INVALID_FILE":
            messagebox.showerror("哎呀呀...", "此miobject模型可能存在格式或内容错误，程序无法正常读取，请检查后重试")
        else:

            st_output.delete("1.0", END)
            st_output.insert("1.0", result[0])
            list_model.delete(0, END)
            list_model.insert(END, "==所含全部模型id==")
            for i in result[1]:
                list_model.insert(1, i)
            list_model.insert(END, "=============")
            if result[2] != {"bk":[],"nf":[]}:
                messagebox.showwarning("转换完成，但出了些问题...", "模型 " + filename.get().split("/")[-1] + " 转换完成！但出现 无法转换模型："+ str(result[2]["bk"])+",已替换为屏障；无法识别模型："+ str(result[2]["nf"])+"，已替换为结构空位")
            else:
                messagebox.showinfo("转换完成", "模型 " + filename.get().split("/")[-1] + " 转换完成！")
    else:
        messagebox.showwarning("提示","你还没有打开任何一个miobject模型呢")

def copy_command():

    # 打开复制粘贴板
    wcb.OpenClipboard()
    # 清空目前 Ctrl + C 复制的内容
    wcb.EmptyClipboard()
    # 将内容写入复制粘贴板，第一个参数是 win32con.CF_TEXT
    # 第二个参数是我们要复制的内容，编码的时候指定为 "gbk"
    wcb.SetClipboardData(1, st_output.get("1.0", "end").encode("gbk"))
    # 关闭复制粘贴板
    wcb.CloseClipboard()

def open_help_docx():
    file_path = convert.get_path("./resource/help_doc.docx")
    os.startfile(file_path)

#主界面
#顶栏菜单
menubar = Menu(root)
root.config(menu=menubar)
file_menu = Menu(menubar, tearoff=False)
#文件菜单项
menubar.add_cascade(label="文件", menu=file_menu)
file_menu.add_command(label="打开miobject模型文件", command=open_file)
info_menu = Menu(menubar, tearoff=False)
#关于菜单项
def open_url_github():
    webbrowser.open("https://github.com/dmh4401/MI_TO_MC_command_transform_tool", new=0)
menubar.add_cascade(label="关于", menu=info_menu)
info_menu.add_command(label="关于此软件", command=open_win_info)
info_menu.add_command(label="使用教程及注意事项", command=open_help_docx)
info_menu.add_command(label="GITHUB源码获取", command=open_url_github)

#标签
text_filename = StringVar()
text_filename.set("当前模型文件：无")
label_filename = Label(root,textvariable=text_filename,anchor="w")
label_filename.place(x=5, y=5, width=400, height=30)
photo_mtm = PhotoImage(file=convert.get_path("./resource/mtm.png"))
label_photo = Label(root,anchor="w",image=photo_mtm)
label_photo.place(x=187, y=25, width=187, height=123)
label_copyright = Label(root,text="BiliBili-@超帅气的指令师CR",anchor="w",font=("黑体", 8, "underline"),foreground="#0600ff")
label_copyright.place(x=10, y=370, width=200, height=30)
label_qq = Label(root,text="QQ交流群496604302",anchor="w",font=("黑体", 8))
label_qq.place(x=280,y=370, width=150, height=30)
# 绑定label单击事件
def open_url_CR(event):
    webbrowser.open("https://space.bilibili.com/40995160", new=0)
label_copyright.bind("<Button-1>", open_url_CR)

#列表
list_model = Listbox(root)
list_model.insert(END, "==所含全部模型id==")
list_model.insert(END, "=============")
list_model.place(x=5, y=35, width=157, height=186)

#复选框
cb_debug_var = BooleanVar()
cb_debug = ttk.Checkbutton(root,text="输出调试日志",variable=cb_debug_var)
cb_debug.place(x=290, y=147, width=100, height=30)
cb_debug_var.set(False)

#按钮
btn_transform = ttk.Button(root, text="开始转换", takefocus=False,command=start_transform)
btn_transform.place(x=180, y=145, width=95, height=30)

btn_copy = ttk.Button(root, text="复制指令结果", takefocus=False,command=copy_command)
btn_copy.place(x=180, y=191, width=193, height=30)

#分割线
ttk.Separator(root).pack(fill="x", pady=5)

#标签框架
lf_output = LabelFrame(root,text="输出结果")
lf_output.place(x=22, y=230, width=361, height=140)

#带条文本框
#会出现 libpng warning: iCCP: known incorrect sRGB profile，但不要紧
st_output=ScrolledText(lf_output)
st_output.pack()



mainloop()