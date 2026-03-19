{  A quick note as of 4-20-2006:  The entire source to Seth's IGM Barak's }
{  house is available for download at pegasus.bbs.us/cvsweb.cgi         }
{  A good place to start if you want to make an easy to install IGM
{  that runs great!    }

{  These are the pascal file structures for the players and enemies for }
{  Legend Of The Red Dragon 4.06 to 4.07 This file was last updated on }
{  4-20-2006.  For software developers.                                  }                                        }
{                                                                       }
{  Legend Of The Red Dragon                                             }
{  (c) Copyright 2006; Metropolis Gameport                              }
{  ALL RIGHTS RESERVED.                                                 }
{                                                                       }
{                                                                       }
{  Note from Seth A. Robinson:  You have my permission to build         }
{  add-ons, editers, whatever - BUT, if you decide to charge money for  }
{  them I would appreciate it if you would upload me your file          }
{  privately, let me evualuate it and see if it deserves my stamp of    }
{  approval.                                                            }
{                                                                       }
{  That's right, I'm not against others making money off their mods, in }
{  fact, I don't demand any percentage whatsoever.  God knows I've made }
{  much more than I deserve already.  Just try not to charge more than  }
{  I do for LORD itself, k?                                             }

{  Also, in ANY util for LORD, be sure to give some credit to ME! <G>   }

{  If you are going to build a LORD In Game Module, you *MUST* meet     }
{  these specifications to call it such:                                }
{                                                                       }
{  1.  It reads *NO* external drop file, but gets all data from the     }
{      info.? file AND node?.dat file.                                  }
{                                                                       }
{  2.  It has options to install *AND* uninstall itself.  (ie, add the  }
{      program to the 3RDPARTY.DAT file itself)                         }
{                                                                       }
{  3.  The top line if the file_id.diz is like this:                    }
{      <NAME & VERSION OF YOUR PROG> LORD IGM  (Decorate if you like)   }   

{  The reason I'm giving these specific instructions is because a few   }
{  others have released their software as IGM's, sysops expect the      }
{  simple installation they got with Barak's House                      }
{  and instead find themselves having to mess with writing dropfiles for}
{  the LORD mod separatly - which can be a mess, especially if the drop }
{  file is overwritten while someone else goes into the realm, ect.     }

{  *PLEASE* abide by these rules.  If you don't - I, uh, will send      }
{  someone to break your thumbs! ;>                                     }

{  Mail and color codes:  A "`" (not a "'") proceeded by certain symbols}
{  and numbers have special funtions when LORD reads them in someones   }
{  mail.  Except for colors, these codes must be at the beginning of a  }
{  line.  Look at some MAILXX.DAT files for examples.  Here is the list }
{  of codes - for instance, you may want your 3rd party program to give }
{  a certain player one more charm point - there is a code to do that!  }

{*

NOTE:  In most cases, such as adding experience, if you put a negetive
amount, it will DECREASE the value.  It does do checking to make sure it's
not less then 1 when done.

`1 through `0, and `! through `% are colors.  (15 of them)
          (`^ was removed.  Who wants all black forground color?)
The following codes MUST be the first and only thing on the line.

`-<account num>  This will have LORD give the 'Write <name> back?' option.
`b<amount> this deposites the amount in the readers bank account.
`G<amount> this puts the amount in the readers 'money in hand'.
`E<amount> this adds to the readers experience by amount.
`?<account num>  Makes user MARRIED to this person. (-1 for not married)
`{ this increments the 'number of lays' stat of the reader.
`} {this increments the readers charm.)
`+<amount>  Users charm BECOMES this number. (Used in divorce mail-backs)
`K this increments the amount of kids the reader has.
`M<amount>  This increments readers Strength
`D<amount>  This increments readers Defence
`,<amount>  This increments forest fights per that day
`:<amount>  This increments user fighters per that day
`;<amount>  This increments readers Hitpoint Max

   (Note, the above mail codes can decrement if a - is placed before num.
   Checking is done to make sure user does not go below certain levels)

`S This raises the readers SKILL in his current class.  Will not let the
   skill pass 40.
`T <account num>  Indicates <account num> wants to flirt with reader
`Y <account num>  Indicates <account num> wants to kiss reader
`U <account num>  Indicates <account num> wants to have dinner with reader
`I <account num>  Indicates <account num> wants to sleep with reader
`P <account num>  Indicates <account num> wants to propose to reader
`O <account num> Begins an online battle with <account num> (Don't use this!)
`c clears, homes the screen and goes down two lines.

     *****  HOW DO I MAKE AN IN GAME MODULE FOR LORD? *****

  It is really sort of easy.  The smartest way is to write your door
  to be able to read the NODEX.DAT files - (For com port, port speed, ect)
  these are text editable, so you should be able to figure them out ok.

  It comes down to this:  Someone will be able to unzip your program, and
  run the CFG/Installer, and it will add two lines to the 3RDPARTY.DAT
  file.  These two lines are ALL LORD needs to automatically list your
  door name as it appears to the players, (second line) and the path and
  name of the EXE or BAT file that is run.  Look at the 3RDPARTY.DAT
  file, it comes empty, but does contain a commented out example.
  Note:  the 3RDPARTY.DAT file is automatically created when LORD is
  run if it doesn't exist.


  Notice that a * anywhere in the first line will have LORD subsitute
  the node number.  So with say "C:\LORD\NEWBAR.EXE /N*" would give your
  program the /N6 parm if node 6 was playing.  LORD will go up to 999
  nodes.  (In theory only <G> )

  Why is this important?  Because you can then retrieve the correct NODEX.DAT
  file yourself from the LORD dir.  LORD will drop a file called INFO.<node
  num>, it contains the account number of the user who just dropped.
  (this file also contains extra data, pherhaps enough so your program
  will not NEED to open another file)

  Your door should pick up that, (it's a text file) and load that record.
  Let them use the door, and write it upon exitting.  This means you could
  load different INFO and NODE data for each node - thereby making your
  addon multi-node.  Simple, eh?

  Another thing.  The max "Add On's" 3.50+ can handle is a lot.  At least a
  thousand.

  Please be considerate enough to throw a 'Uninstall' option in your
  configure program - To find your two lines and strip them out, just
  in case the sysop decides not to keep it.  Sure, most sysops can edit
  the 3RDPARTY.DAT file themselves, but it's a nice option anyway.

  There you have it - The goal of this is to make installing add-ons
  much easier then installing a whole new door, because they will not
  have to re-configure any com port settings, or node settings, because
  you will be reading the NODEX.DAT files.  This also means you don't
  have to mess with drop files at all, since using the 'account number'
  from the INFO.??? file lets you load the entire account, including their
  BBS handle and LORD handle of course.

  The structure of the LORD.<node num> file:

  13      <-Account, from 0 to 149
  3       <-Graphic Setting, 3 is ANSI, less is ASCII
  RIP YES <-Obvious - It's RIP NO when they are not RIP.
  FAIRY YES <- Do they have a fairy with them?
  Time Left <- In minutes.  This is READ AGAIN when they come back.  You
               should keep track and change this number accordingly, so LORD
               will how much time to give them.
  LORD Handle       \
  Real First Name    \
  Real Last Name      \
  Com Port;           |  Other info you may find useful.  You should still 
  Caller Baud Rate;  /   read the NODEX.DAT files, because they contain
  Port Baud Rate    /    more info - Such as a nonstardard com port.
  
  -=-=New things added to the info.? file in 3.26=-=-
  Note:  LORD never reads any of these in, only writes them for your
  convenience.

  FOSSIL  <- (will say INTERNAL if they are using LORD's internal routines)
  REGISTERED <- LORD registration status, else UNREGISTERED.
  CLEAN MODE ON <- else CLEAN MODE OFF

  NOTE:  Look at the INFO.? file yourself while someone is in a In
  Game Module from LORD, you'll notice there are NO spaces in the file.

}
program LordStrc;
uses dos,crt;




 {player record}
 type player_info = record
   names          : string[20]; {name in the game}
   real_names     : string[50]; {name from the bbs}
   hit,                         {current hit points}
   bad,                         {did player divorce today?}
   rate,                        {how many days has player been gone?}
   hit_max        : integer;    {max hp}
   weapon_num     : integer;    {wep num}
   weapon         : string[20]; {wep name}
   seen_master    : integer;    {5 = true, else 0}
   fights_left    : integer;    {forest fights}
   human_left     : integer;    {human fights}
   gold           : longint;    {gold in hand}
   bank           : longint;    {gold in bank}
   def            : integer;    {total def points}
   strength       : integer;    {total str points}
   charm          : integer;    {hrmmmm}
   seen_dragon    : integer;    {5=true}
   seen_violet    : integer;    {5=true}
   level          : integer;    {hmmmm}
   time           : word;       {day # player was last on}
   arm            : string[20]; {armor name}
   arm_num        : integer;    {armor num}
   dead           : shortint;   {5=true}
   inn            : shortint;   {player sleeping at inn? 5=true}
   gem            : integer;    {# of gems on hand}
   exp            : longint;    {xp points}
   sex            : shortint;   {0=male,5=female, else well..}
   seen_bard      : shortint;   {5=true}
   Who_knows      : integer;    {day num # player was last reincarnated}
   Who_cares      : integer;    {player lays stat}
   Why            : integer;    {if 1 then player has gotten "magically delicious" today}
   on_now         : boolean;    {is player on?}
   m_time         : integer;    {day on_now statwas last used}
   time_on        : string[5];  {time he came in}
   class          : shortint; {1=warrior, 2=mystic, 3=theif}
   horse          : integer;    {if 1 then horse}
   love           : string[25]; {**not used}
   married        : integer;    {not used. use married_to instead.}
   kids           : integer;    {# of kids}
   king           : integer;    {# of times player has won game}
   skillw         : shortint;   {number of Death Knight skill points}
   skillm         : shortint;   {number of Mystical skill points}
   skillt         : shortint;   {number of Thieving skill points}

   levelw         : shortint;   {number of Death Knight skill uses left today}
   levelm         : shortint;   {number of Mystical skill uses left today}
   levelt         : shortint;   {number of Thieving skill uses left today}

   inn_random     : boolean;    {not used}
   married_to     : integer;    {-1 if not married, else num of other player}
   v1             : longint;    {# of times player has transfered gold that day}
   v2             : integer;    {# of player kills}
   v3             : integer;    {if 5, wierd event in forest will happen}
   v4             : boolean;    {is player in high spirits? (can do jennie)}
   v5             : shortint;   {if 5, player has flirted that day}
   new_stat1      : shortint;   {these 3 are unused by lord.}
   new_stat2      : shortint;   {however, npclord messes with all 3}
   new_stat3      : shortint;   {}


{  Remember, in 3.20+ player skill points for each class can reach 40.      }

{  It's ok to have your editer change the player level to say, 12 or        }
{  such, LORD will automatically not let the player play if the game is     }
{  not registered.                                                          }

{  If in your program you let the player get a new weapon, remember, you CAN}
{  change the name of his weapon,  but the weapon NUMBER stat is what tells }
{  LORD which weapon he has, and if he sells it, will SUBTRACT the correct  }
{  number from his overall strength.  Kind of complicated.  Armour works the}
{  exact same way.                                                          }

Weapon Structures for weapons.dat

  weparm_rec = record
    name  : string; {shouldnt excede 30 chars! (After colors) }
    price : longint; {the price of the item }
    num   : longint; {strength needed to buy weapon }
  end;

Armor structures for armor.dat

  weparm_rec = record
    name  : string; {shouldnt excede 30 chars! (After colors) }
    price : longint; {the price of the item }
    num   : longint; {defense needed to buy armor }
  end;


  {forest monster record format}
 type monst = record
           name: string[60];
           strength: longint;
           gold: longint;
           weapon: string[60];
           exp_points: longint;
           hit_points: longint;
           death: string[100]; {shown when monster is killed by power move}
 end;

{  There are eleven monsters for each level - they are in the file in order.}
{                                                                           }
{  You cannot ADD monsters, but you can change them.  Or one possibilty     }
{  would to write an .EXE that is run before LORD is played each time that  }
{  randomly replaces some monsters in each level with new ones.             }
{                                                                           }

Everytime a user enters an IGM, LORD creates a file called OUT.<player num>.
This a text file.  The first line is the description LORD will give someone
when they view 'who's online' or try to attack them.

The addition: 

You can let people exit straight back to the BBS by making the second line
read QUIT.  Specifying something else will now have LORD log them off, and
automatically return to THAT command line specified on they're next log on.

So if you rewrote the out.1 file while player num 1 was in your IGM like 
this:

is sleeping in Barak's house.
c:\barak\barak.exe *  

Then LORD would actually let that person stay at Barak's.  Specifying a 
second line also makes LORD display 'where they are' slightly differently so  
a 'who is online' would look like this:

Billy Bob is sleeping in Barak's house. 

No one can attack someone who is 'out of the realm' so be careful if you
use this function.  Note:  Before return a user to your IGM when they log
on the next day or whenever, it processes mail and "new day" routines if
needed. 

********* ABOUT MAINT.BAT ***********
This is a batch file run every day RIGHT AFTER LORD does its maint.  This
way you could run your IGM's maint, or add things to the daily log in LORD
ect, BEFORE anyone plays that day.                                        
                              
If you want to use this, do the following in your install program:

1. See if maint.bat exists.  If it doesn't, assume they are running an older
version, and tell them to  get 4.07.

2. Check to see what is already in the MAINT.BAT file, if your IGM name or
whatever program you use is ALREADY in there, don't add it again, take it
out if you need to and add a different line, or just leave the old one in.

3. When someone uses the UNINSTALL option, make sure your program takes out
the additions in MAINT.BAT in a non destructive way.  Don't screw up another
IGM's stuff above or below yours.  Just like the 3rdparty.dat file, really.

4.  In your maint or whatever, display some kind of progress report, and the
IGM's name.  Sysops like to know what they are doing, if they happen to be
watching at midnight, give them a treat.  Don't clear the screen if you can
help it.  And DON'T require a keypress to continue or anything.

Also, it is technically possible to RUN an IGM this way - it creates an
INFO.? file just like normal.   Not sure how this would be handy but..


********** INFO ON BADWORDS.DAT *********

Check this file out, you'll understand it easily.  A thought is to run this
by all user inputs in your IGM, that way the 'swear patrol' is online even
out of LORD.  This ain't required, but hey it would be cool.

}

end.
