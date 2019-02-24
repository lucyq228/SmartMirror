
import tkinter as tk
from tkinter import ttk #progress bar
import datetime #to show Pomodoro time only for today
from datetime import date, timedelta

xlarge_text_size = 58 #94
large_text_size = 42 #48
medium_text_size = 28 #28
small_text_size = 16 #18
xsmall_text_size = 8 #new

class Timer():
    def __init__(self, master, background="black"):
        self.master = master
        master.title('Pomodoro Timer')

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

        # self.tk = Tk()
        # self.tk.configure(background = 'black')

        self.display = tk.Label(master, height=2, width=50,
                                font=('Helvetica', xsmall_text_size), bg='black', fg='gray')
        self.display.config(text='00:00')
        self.display.grid(row=0, column=0, columnspan=5)

        # progress bar & the style
        s = ttk.Style()
        s.theme_use('clam')
        s.configure('Horizontal.TProgressbar', troughcolor='black', background='white')  # foreground='white',
        self.pb = ttk.Progressbar(self.master, style='Horizontal.TProgressbar', orient='horizontal',
                                  mode='determinate', length=40)  # length=360,self.displayFrm
        self.pb.grid(columnspan=5, sticky=tk.W+tk.E)

        # buttons
        self.start_button = tk.Button(master, font=('Helvetica', xsmall_text_size), bg='black', fg='white',
                                      text='Pomodoro', width=8, height=2, command=self.start)  # self.displayFrm
        self.start_button.grid(row=2, column=0)

        self.start_button_10 = tk.Button(master, bg='black', font=('Helvetica', xsmall_text_size), fg='white',
                                         text='10 mins', width=8, height=2, command=self.start_10)  # self.displayFrm
        self.start_button_10.grid(row=2, column=1)

        self.start_button_60 = tk.Button(master, bg='black', font=('Helvetica', xsmall_text_size), fg='white',
                                         text='60 mins', width=8, height=2, command=self.start_60)  # self.displayFrm
        self.start_button_60.grid(row=2, column=2)

        self.pause_button = tk.Button(master, font=('Helvetica', xsmall_text_size), bg='black', fg='white',
                                      text='Reset', width=8, height=2, command=self.reset,
                                      state='disabled')  # self.displayFrm
        self.pause_button.grid(row=2, column=3)

        self.complete_button = tk.Button(master, font=('Helvetica', xsmall_text_size), bg='black', fg='white',
                                         text='Complete', width=8, height=2, command=self.complete,
                                         state='disabled')  # self.displayFrm
        self.complete_button.grid(row=2, column=4)


        # time tracking

        self.tracking_bttn = tk.Button(master, bg='black', font=('Helvetica', xsmall_text_size), fg='white',
                                      text='Today\'s Pomodoro Time: 0 min', width=8, height=2,
                                       state='disabled')
        self.tracking_bttn.grid(columnspan=5, sticky=tk.W+tk.E)
        self.min_init2 = 0

        # countdown
        self.countdown()

        # today's date for time tracking restart
        self.today = datetime.datetime.today().strftime('%Y-%m-%d')

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

root = tk.Tk()
my_timer = Timer(root)

root.mainloop()