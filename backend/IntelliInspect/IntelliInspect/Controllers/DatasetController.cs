using Microsoft.AspNetCore.Mvc;

namespace IntelliInspect.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class DatasetController : ControllerBase
    {
        [HttpPost("upload")]
        public IActionResult UploadDataset(IFormFile file)
        {
            if (file == null || file.Length == 0)
                return BadRequest("No file provided.");

            if (!file.FileName.EndsWith(".csv"))
                return BadRequest("Invalid file format. Only .csv files are accepted.");

            // 👇 You will add logic to forward file to ML service here
            return Ok("File uploaded successfully.");
        }
    }
}
