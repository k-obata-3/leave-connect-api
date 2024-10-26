const utils = {
  getLocalCurrentDate() {
    const utcDate = new Date();
    const timezoneOffset = utcDate.setHours(utcDate.getHours() + 9);
    return new Date(utcDate.getHours() + timezoneOffset)
  },

  getUtcCurrentDate() {
    return new Date();
  },

  getLocalDate(dateStr: string) {
    const utcDate = new Date(dateStr);
    const timezoneOffset = utcDate.setHours(utcDate.getHours() + 9);
    return new Date(utcDate.getHours() + timezoneOffset)
  },

  getUtcDate(dateStr: string) {
    return new Date(dateStr);
  },

  getDateString(dateVal: Date, separator: string) {
    let localDate = dateVal.toLocaleDateString().split('/');
    let year = localDate[0];
    let month = "0" + localDate[1];
    let date = "0" + localDate[2];

    return `${year}${separator}${month.slice(-2)}${separator}${date.slice(-2)}`;
  },

  getTimeString(dateVal: Date) {
    let localDate = dateVal.toLocaleTimeString().split(':');
    let hours = "0" + localDate[0];
    let minutes = "0" + localDate[1];
    return `${hours.slice(-2)}:${minutes.slice(-2)}`;
  },

  getServiceYears(referenceDate: Date) {
    if(!referenceDate) {
      return null;
    }
    let dateNow = this.getLocalCurrentDate();
    let timeDiff = dateNow.getTime() - referenceDate.getTime();
    let daysDiff = timeDiff / (1000 * 3600 * 24);
    const DAYS_PER_MONTH = 365 / 12;
    let year = Math.floor(daysDiff / 365);
    let month = Math.floor((daysDiff - 365 * year) / DAYS_PER_MONTH);
    // let day = Math.floor((daysDiff - 365 * year - DAYS_PER_MONTH * month));
    return `${year}年${month}ヶ月`
  },

  getElapsedYears(referenceDate: Date) {
    if(!referenceDate) {
      return 0;
    }

    return this.getLocalCurrentDate().getFullYear() - referenceDate.getFullYear();
  },

  getElapsedMonths(referenceDate: Date) {
    if(!referenceDate) {
      return 0;
    }

    const year: number = this.getElapsedYears(referenceDate);
    const month: number = this.getLocalCurrentDate().getMonth() - referenceDate.getMonth();
    return year * 12 + month;
  },

  getApplicationHour(totalTime: number) {
    if(totalTime == 8) {
      return 1.0;
    } else if(totalTime == 4) {
      return 0.5;
    } else {
      return 0.125 * totalTime;
    }
  }

}
module.exports = utils;