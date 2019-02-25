
import tkinter as tk
from tkinter import ttk #progress bar
import datetime #to show Pomodoro time only for today


LARGE_FONT = ("Verdana", 12)
xsmall_text_size = 8 #new

class infoFrame(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self, background='black')

        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (Timer, PageOne, PageTwo):
            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(Timer)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


class Timer(tk.Frame):

    def __init__(self, master, controller):
        tk.Frame.__init__(self, master)

        self.master = master

        self.state = False
        self.minutes = 25  # 25
        self.seconds = 0

        self.mins = 25  # 25
        self.secs = 0

        self.minutes_10 = 10
        self.seconds_10 = 0

        self.mins_10 = 10
        self.secs_10 = 0

        self.minutes_60 = 60
        self.seconds_60 = 0

        self.mins_60 = 60
        self.secs_60 = 0

        self.displayFrm = tk.Frame(self, bg='black')
        self.displayFrm.pack(side = 'top', anchor = 'w', pady =10) #pady =50
        self.display = tk.Label(self.displayFrm, height=2, width=40,
                                font=('Helvetica', xsmall_text_size), bg='black', fg='gray')
        self.display.config(text='00:00')
        self.display.pack(side='top', anchor='n')

        # progress bar & the style
        s = ttk.Style()
        s.theme_use('clam')
        s.configure('Horizontal.TProgressbar', troughcolor='black', background='white')  # foreground='white',
        self.pb = ttk.Progressbar(self, style='Horizontal.TProgressbar', orient='horizontal',
                                  mode='determinate', length=280)  # length=360,self.displayFrm
        self.pb.pack(side='top', anchor='n')

        # label = tk.Label(self, bg='black', font=('Helvetica', xsmall_text_size), fg='white',
        #                               text='Start page --- Timer', width=40, height=8)
        # label.pack(pady=10, padx=10)

        # buttons
        self.start_button = tk.Button(self.displayFrm, font=('Helvetica', xsmall_text_size), bg='black', fg='white',
                                      text='Pomodoro', width=8, height=2, command=self.start)  # self.displayFrm
        self.start_button.pack(side='left', anchor='e')

        self.start_button_10 = tk.Button(self.displayFrm, bg='black', font=('Helvetica', xsmall_text_size), fg='white',
                                         text='10 mins', width=8, height=2, command=self.start_10)  # self.displayFrm
        self.start_button_10.pack(side='left', anchor='e')

        self.start_button_60 = tk.Button(self.displayFrm, bg='black', font=('Helvetica', xsmall_text_size), fg='white',
                                         text='60 mins', width=8, height=2, command=self.start_60)  # self.displayFrm
        self.start_button_60.pack(side='left', anchor='e')

        self.pause_button = tk.Button(self.displayFrm, font=('Helvetica', xsmall_text_size), bg='black', fg='white',
                                      text='Reset', width=8, height=2, command=self.reset,
                                      state='disabled')  # self.displayFrm
        self.pause_button.pack(side='left', anchor='e')

        self.complete_button = tk.Button(self.displayFrm, font=('Helvetica', xsmall_text_size), bg='black', fg='white',
                                         text='Complete', width=8, height=2, command=self.complete,
                                         state='disabled')  # self.displayFrm
        self.complete_button.pack(side='left', anchor='e')

        # time tracking
        self.tracking_bttn = tk.Button(self, bg='black', font=('Helvetica', xsmall_text_size), fg='white',
                                       text='Today\'s Pomodoro Time: 0 min', width=40, height=2,
                                       state='disabled')
        self.tracking_bttn.pack(side='top', anchor='n')
        self.min_init2 = 0

        # add next button
        # self.next_bttn = tk.Button(master, font=('Helvetica', xsmall_text_size), bg='black', fg='white',
        #                            text='>>>>', width=8, height=1, anchor='e')  # ,
        # command=lambda: controller.show_frame(textReview)
        # self.next_bttn.grid(columnspan=5, sticky=tk.W + tk.E)

        # countdown
        self.countdown()

        # today's date for time tracking restart
        self.today = datetime.datetime.today().strftime('%Y-%m-%d')

        #button to the next page
        button = tk.Button(self, text=">>>>", font=('Helvetica', xsmall_text_size), bg='black', fg='white',
                           command=lambda: controller.show_frame(PageOne))
        button.pack(side="right", anchor='e')

    def countdown(self):
        # Displays a clock starting at min:sec to 00:00, ex: 25:00 -> 00:00
        self.today2 = datetime.datetime.today().strftime('%Y-%m-%d')  # check date when doing countdown

        if self.state == True:
            if self.secs < 10:
                if self.mins < 10:
                    self.display.config(text='0%d : 0%d......%d mins' % (self.mins, self.secs, self.min_init))
                else:
                    self.display.config(text='%d : 0%d......%d mins' % (self.mins, self.secs, self.min_init))
            else:
                if self.mins < 10:
                    self.display.config(text='0%d : %d......%d mins' % (self.mins, self.secs, self.min_init))
                else:
                    self.display.config(text='%d : %d......%d mins' % (self.mins, self.secs, self.min_init))

            # when complete:
            if (self.mins == 0) and (self.secs == 0):
                self.display.config(text="Complete!")
                self.complete_button['state'] = 'disabled'  # when complete, can only reset
                if self.today == self.today2:
                    self.min_init2 += self.min_init
                    self.tracking_bttn['text'] = 'Today\'s Pomodoro Time: ' + str(self.min_init2) + ' min'
                else:
                    self.today = datetime.datetime.today().strftime('%Y-%m-%d')
                    self.min_init2 = 0
                    self.min_init2 += self.min_init
                    self.tracking_bttn['text'] = 'Today\'s Pomodoro Time: ' + str(self.min_init2) + ' min'

                self.state = False
                self.minutes = 25  # 25
                self.seconds = 0

                # self.mins = 25  # 25
                # self.secs = 0

                self.minutes_10 = 10
                self.seconds_10 = 0

                # self.mins_10 = 10
                # self.secs_10 = 0

                self.minutes_60 = 60
                self.seconds_60 = 0

                # self.mins_60 = 60
                # self.secs_60 = 0

            else:
                if self.secs == 0:
                    self.mins -= 1
                    self.secs = 59
                else:
                    self.secs -= 1

                self.pb['value'] = self.mins * 60 + self.secs
                self.master.after(1000, self.countdown)
        else:
            self.master.after(100, self.countdown)

    def start(self):  # Pomodoro
        # check date when doing countdown
        self.today2 = datetime.datetime.today().strftime('%Y-%m-%d')

        if self.state == False:
            self.state = True
            self.mins = self.minutes
            self.secs = self.seconds
            self.pb['value'] = 0
            self.pb['maximum'] = self.minutes * 60
            self.min_init = self.mins

            # clean up yesterday records
            if self.today != self.today2:
                self.tracking_bttn['text'] = 'Today\'s Pomodoro Time: 0 min'

        if self.state == True:
            self.complete_button['state'] = 'normal'
            self.pause_button['state'] = 'normal'
            self.start_button['state'] = 'disabled'
            self.start_button_10['state'] = 'disabled'
            self.start_button_60['state'] = 'disabled'

    def start_10(self):
        # check date when doing countdown
        self.today2 = datetime.datetime.today().strftime('%Y-%m-%d')

        if self.state == False:
            self.state = True
            self.mins = self.minutes_10
            self.secs = self.seconds_10
            self.pb['value'] = 0
            self.pb['maximum'] = self.minutes_10 * 60
            self.min_init = self.mins
            # clean up yesterday records
            if self.today != self.today2:
                self.tracking_bttn['text'] = 'Today\'s Pomodoro Time: 0 min'

        if self.state == True:
            self.complete_button['state'] = 'normal'
            self.pause_button['state'] = 'normal'
            self.start_button['state'] = 'disabled'
            self.start_button_10['state'] = 'disabled'
            self.start_button_60['state'] = 'disabled'

    def start_60(self):
        # check date when doing countdown
        self.today2 = datetime.datetime.today().strftime('%Y-%m-%d')

        if self.state == False:
            self.state = True
            self.mins = self.minutes_60
            self.secs = self.seconds_60
            self.pb['value'] = 0
            self.pb['maximum'] = self.minutes_60 * 60
            self.min_init = self.mins
            # clean up yesterday records
            if self.today != self.today2:
                self.tracking_bttn['text'] = 'Today\'s Pomodoro Time: 0 min'

        if self.state == True:
            self.complete_button['state'] = 'normal'
            self.pause_button['state'] = 'normal'
            self.start_button['state'] = 'disabled'
            self.start_button_10['state'] = 'disabled'
            self.start_button_60['state'] = 'disabled'

    def reset(self):
        if self.state == True:
            self.state = False
            self.display.config(text='00:00')
            self.pb['value'] = 0
            self.pb['maximum'] = 0

            self.minutes = 25  # 25
            self.seconds = 0
            self.mins = 25  # 25
            self.secs = 0
            self.minutes_10 = 10
            self.seconds_10 = 0
            self.mins_10 = 10
            self.secs_10 = 0
            self.minutes_60 = 60
            self.seconds_60 = 0
            self.mins_60 = 60
            self.secs_60 = 0

            self.complete_button['state'] = 'disabled'
            self.pause_button['state'] = 'disabled'
            self.start_button['state'] = 'normal'
            self.start_button_10['state'] = 'normal'
            self.start_button_60['state'] = 'normal'

        else:
            # state is false, as timer is completed
            self.display.config(text='00:00')
            self.pb['value'] = 0
            self.pb['maximum'] = 0
            self.countdown()  # make countdown available

            # bttn unavailable so the user has to click 'reset' to start
            self.complete_button['state'] = 'disabled'
            self.pause_button['state'] = 'disabled'
            self.start_button['state'] = 'normal'
            self.start_button_10['state'] = 'normal'
            self.start_button_60['state'] = 'normal'

    def complete(self):
        self.today2 = datetime.datetime.today().strftime('%Y-%m-%d')

        if self.state == True:

            # clean up yesterday records
            if self.today != self.today2:
                self.min_init2 = 0
                self.min_init2 += self.min_init
                self.tracking_bttn['text'] = 'Today\'s Pomodoro Time: ' + str(self.min_init2) + ' min'
            else:
                self.min_init2 += self.min_init
                self.tracking_bttn['text'] = 'Today\'s Pomodoro Time: ' + str(self.min_init2) + ' min'

            self.state = False
            self.display.config(text='00:00')
            self.pb['value'] = 0
            self.pb['maximum'] = 0

            self.minutes = 25  # 25
            self.seconds = 0
            self.mins = 25  # 25
            self.secs = 0
            self.minutes_10 = 10
            self.seconds_10 = 0
            self.mins_10 = 10
            self.secs_10 = 0
            self.minutes_60 = 60
            self.seconds_60 = 0
            self.mins_60 = 60
            self.secs_60 = 0

            # after clicking complte or reset, only the other three buttns available
            self.complete_button['state'] = 'disabled'
            self.pause_button['state'] = 'disabled'
            self.start_button['state'] = 'normal'
            self.start_button_10['state'] = 'normal'
            self.start_button_60['state'] = 'normal'

        else:
            # state is false, as timer is completed
            self.display.config(text='00:00')
            self.pb['value'] = 0
            self.pb['maximum'] = 0
            # self.countdown() #make countdown available

            self.start_button['state'] = 'normal'
            self.start_button_10['state'] = 'normal'
            self.start_button_60['state'] = 'normal'


class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        # label = tk.Label(self, text="Page One!!!", font=LARGE_FONT)
        label = tk.Label(self, bg='black', font=('Helvetica', xsmall_text_size), fg='yellow',
                         text='Page 1 --- code review', width=40, height=8)
        label.pack(pady=10, padx=10)

        self.bttn_frame = tk.Frame(self, bg='black')
        self.bttn_frame.pack(side='bottom', anchor ='n')

        self.bttn_frame1 = tk.Frame(self.bttn_frame, bg="black")
        self.bttn_frame1.pack(side='left', anchor='w')
        button1 = tk.Button(self.bttn_frame1, text="<<<<", font=('Helvetica', xsmall_text_size), bg='black', fg='white',
                            command=lambda: controller.show_frame(Timer))
        button1.pack(side="left", anchor='w')


        self.bttn_frame2 = tk.Frame(self.bttn_frame, bg="black")
        self.bttn_frame2.pack(side='left', anchor='e')
        button2 = tk.Button(self.bttn_frame2, text=">>>>", font=('Helvetica', xsmall_text_size), bg='black', fg='white',
                            command=lambda: controller.show_frame(PageTwo))
        button2.pack(side="right", anchor='e')


class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        # label = tk.Label(self, text="Page Two!!!", font=LARGE_FONT)
        label = tk.Label(self, bg='black', font=('Helvetica', xsmall_text_size), fg='white',
                         text='Page 2 --- google calendar', width=40, height=8)
        label.pack(pady=10, padx=10)

        button2 = tk.Button(self, text="<<<<", font=('Helvetica', xsmall_text_size), bg='black', fg='white',
                            command=lambda: controller.show_frame(PageOne))
        button2.pack(side="left", anchor='w')


app = infoFrame()
app.mainloop()

