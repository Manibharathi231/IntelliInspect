namespace IntelliInspect.Models
{
    public class DateRangeRequest
    {
        public string TrainStart { get; set; }
        public string TrainEnd { get; set; }
        public string TestStart { get; set; }
        public string TestEnd { get; set; }
        public string SimStart { get; set; }
        public string SimEnd { get; set; }
    }
}
