"""Curated vocabulary supplement for ordinary conversation (RU/EN).

The shipped frequency corpus and n-gram weights remain unchanged. These
entries are explicitly reviewed spellings, not synthetic frequency counts.
A short-word collision is resolved only with established target-language
context; normal English words and recognized abbreviations are not overridden.
"""

RU_WORDS = frozenset((
    "а ага ага-ага ай ай-ай апаю апдейт апнул апнуть ау афк ах ахах ахаха б баг баги "
    "багфикс бб без благодаря блин блинский блинчики брр бы в вайб вам вапще вас вау ваще "
    "вблизи ввиду вглубь вдали вдоль ведь видос видосик винда виндовый виндой винду включая "
    "вместо вне внутри во возле вокруг вон вопреки вопще вот вп впн все вслед вследствие "
    "всё вчерась вы гав гг где гл гм гуд да даа даже дебаг дебажить девайс девайсы "
    "дефис дефисы для до "
    "дык его едва ее ей если её ж же жестко жесть жиз жиза жоско жосткий жостко жёсткий "
    "жёстко за завтр завтра запушить зато зафиксить зачем зачет зачот зачёт звин здарова "
    "здорова здрасте здрасьте и ибо из извини изи изо или им имба имбовый имхо инет "
    "интернет исключая итак их к кабы кайф кайфанул кайфово как какбы канеш канешн капец "
    "касательно кек кекек ко когда коммит коммитить комп компик конечно конфа конфиг "
    "конфиги конфы короч короче кринге кринж кроме крч кста кто куда лаг лагает лаги ладн "
    "лан легчайший ли либо линукс линух лишь лол лолкек лул лулз ль мб мдя меж между мем "
    "мемас мемасик мемчик мердж мерджить мерж мимо мне мну мня мобила мобилка мобилку мож "
    "может можн мой мона мы мя мяу на навстречу над надоб надоть нам напротив нас насчет "
    "насчёт начиная не неа немогу немож ненадо непонятки несмотря нзч ни низзя низя нинада "
    "ниче ничо ничосе ничоси ничё ништяк но норм нормас нормик нормуль ноут ноутбук нп ну "
    "ну-ну нуачо нуб нубас нубик нуу ня ням о об обо ого огонь ой ой-ой ок окей окейно "
    "окейчик около он она они оно от откуда относительно ото отпад офигенно офигеть офк ох "
    "оч очнь пасиб пасиба пасибо перед пж пжл пздц пинг пинги пипец плз плиз по поверх "
    "погоди под пока помимо пон понял понятно поперек поперёк после посредством поч почем "
    "почему ппц пред при прив приветик прикол прикольно про прога проги прокси против пулл "
    "пускай пусть пуш пушить ради репа репозиторий рофл рофлить рофлишь рофлю с сабж сабжик "
    "сам сама сами сверх свой сей сие сия сквозь скрин скринчик скриншот со согласно "
    "соединитель соединители сори "
    "сорри сорян софт софтина спасиб спасибки спасибочки спок спс спустя среди сча счас ся "
    "сёдня сёня так также такс там твой те тебе тел телек телик тем тильт тильтанул тип "
    "тест типо то тоже ток тока токс токсик только топчик тормозня треш трэш тут ты тьфу тя у "
    "убунта убунту угу уж ура уф ух ухаха фига фигасе фигня фикс фиксить фича фичи фотка "
    "фоточка фпс фу ха ха-ха хаха хех хз хихи хм хотя хоч хочу хош хошь хрен хрень хы че "
    "че-нить чем ченить через чет чето чил чилить чилл чо чонить чот чото чрез что чтоб "
    "чтобы чтоль чуток чё чё-нить чёт чёто шас шо шо-то шоб шото што штоб шустро шустрый ща "
    "щаз щас щасик що щото щяс ых ыы ыыы эй эт эта это эх юзал юзать юзаю юзер юзеры я ёк "
    "ёлки ёмаё ёпт "
).split())

EN_WORDS = frozenset((
    "a aboard about above across afaik afk after against ah aight all along alongside alr "
    "alright am amid among an any are around as asap at aw be before behind below beneath "
    "beside between beyond brb bro bruh btw bug bugfix bugs but by can cause cheers commit "
    "commits committing concerning config configs congrats cos coz cuz cya dang darn debug "
    "debugger debugging def defs despite dev devs did do dokey dude dunno during eh except "
    "fam feature features ffs for fps fr from ftw fyi geez gg gif gifs gimme gl gnome go "
    "gonna gotcha gotta grats gz ha had hah haha hahaha hardware has he heh hehe her hey hf "
    "hi him his hm hmm hotfix how huh i idk if imho imo in inside into irl is it jeez jk "
    "kate kde kek kinda kubuntu lag laggy lags latency legit lemme linux lmao lmfao lol lolz lul "
    "lulz may me meh meme memed memes merge merged merging my nah near newbie ngl no noob "
    "nope not notwithstanding now np nvm obvs of off oh ok okay okey omg on one onto oof "
    "oops or ouch our out outside over ow per ping pls plz pog probs prolly proxies proxy "
    "pull pulls push pushed pushing regarding repo repos rip rly rn rofl she sheesh since "
    "smh so software sorta soz srsly sry sup sus tbh thanks thanx the thnx tho through "
    "throughout thru thx till tldr to too toward towards ttyl ttyt ty tyvm ubuntu ugh uh um "
    "under underneath until up upon us versus via vpn wanna was wayland we whatcha whew who "
    "whoa why with within without wow wtf xd ya yall yay ye yeah yeet yep yes yet yikes yo "
    "you yup "
).split())

WORDS = {"ru": RU_WORDS, "en": EN_WORDS}
SHORT = {lang: frozenset(w for w in words if 1 <= len(w) <= 3)
         for lang, words in WORDS.items()}

# Some corpus entries are rare Latin abbreviations rather than everyday
# words. Permit these exact collisions only in established Russian context.
# Never override common English words such as of, he, as, at, in or by.
RU_CONTEXT_COLLISIONS = {
    "bp": "из", "lj": "до", "cj": "со", "dj": "во", "rj": "ко",
    "lf": "да", "ye": "ну", "ds": "вы", "ns": "ты", "tt": "ее",
    "oj": "що", "jr": "ок", "ae": "фу", "fe": "ау",
    "j,": "об", "x`": "чё", "g;": "пж", "b[": "их", "t`": "её",
}

# Lowercase corpus acronyms that collide with a very common Russian word.
# Allow the exact spelling in neutral/mixed context, but not after two
# English words. Uppercase acronyms remain protected by Detector.decide.
RU_LOWERCASE_COLLISIONS = {"ghb": "при"}


# Short, common function words and unmistakable conversational forms may begin
# a new language even after a sentence in the previous language. The source
# must not be a dictionary word; all stop-rules in Detector.decide still apply.
TRANSITION_SHORT = {
    "ru": frozenset((
        "на по до от из за об со во ко но не ни бы же ли да ну то уж "
        "мы вы ты он ей им их ах ой ох эх ай ау эй ух ха хм фу "
        "че чё чо шо що ща щас крч кста пж спс хз мб лан ага угу неа"
    ).split()),
    "en": frozenset((
        "as at by in of on to up so no or an am be do go he is it me my us we if "
        "hi oh ah ok yo uh um eh ha ow aw"
    ).split()),
}


# Frequent ordinary words that may be uppercase in prose, including short
# function words. A dictionary match in the source language always wins.
# Unknown all-caps tokens still keep the abbreviation guard.
UPPERCASE_WORDS = {
    "ru": TRANSITION_SHORT["ru"] | frozenset((
        "вот там тут так как кто где что чем уже еще ещё все всё "
        "это эта эти этот тот та те мой моя мое моё твой наш ваш "
        "свой сам сама сами они оно нас вам вас ему ему ей их "
        "нет да был была были быть есть или если надо пора "
        "день ночь мир дом год друг дело язык текст план факт "
        "рука нога вода кофе хлеб соль кино игра тест"
    ).split()),
    "en": TRANSITION_SHORT["en"] | frozenset((
        "the and but for not yes you your they them then than that this "
        "what when where why how who whom with from into over only also "
        "some more most much many both each such very well good bad "
        "here there next last time word text work test file name "
        "make take give keep read write look know want need come "
        "went back down left right like just even same new old "
        "true real long short line code kate"
    ).split()),
}
